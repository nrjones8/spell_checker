# Nick Jones

import re
import sys
from heapq import heappush, heappushpop
# Use nltk's built-in libraries for other tasks
from nltk.tokenize import wordpunct_tokenize
from nltk.stem.porter import PorterStemmer

class SpellChecker:

	def __init__(self, dict_location = '/usr/share/dict/words'):
		# Read in dictionary, strip newlines from each word
		self.dictionary = self.get_dictionary(dict_location)

		# Of the form 'a' => {4 => set(<4 letter words starting with 'a'>), 5 => set()} etc.
		# i.e. index words by their starting letter and length
		# Note that this is a pretty big assumption, but we assume that any user error in
		# spelling came after the first letter
		self.letter_and_length_dictionary = self.preprocess_dictionary(self.dictionary)
		self.io = CheckerIO()
		self.stemmer = PorterStemmer()

	def get_dictionary(self, dict_location):
		'''
		Return a set of words found in <dict_location>, where each word is assumed to be on its own line
		'''
		return set([w.strip() for w in file(dict_location).readlines()])

	def preprocess_dictionary(self, full_dict):
		'''
		Create a dictionary indexed by start letter and word length from the words in <full_dict>
		See above (self.letter_and_length_dictionary) for an example
		'''
		first_letter_to_length_words = {}
		for word in full_dict:
			word_len = len(word)
			first_letter_to_length_words.setdefault(word[0], {})
			first_letter_to_length_words[word[0]].setdefault(word_len, set()).add(word)

		return first_letter_to_length_words

	def get_closest_words(self, word, cands, k = 5):
		'''
		Returns <word> if <word> is in self.dictionary, or the closest <k>
		words measured by the <edit_distance> function
		'''
		if word in self.dictionary:
			return word
		else:
			# Each entry (word, - distance), since it's a min heap
			candidate_dists = []
			
			for cand in cands:
				cand_dist = edit_distance(word, cand)
				if len(candidate_dists) < k:
					heappush(candidate_dists, (- cand_dist, cand))
				else:
					# "peek" at largest distance element, discard it if larger than 
					# cand_dist
					if candidate_dists[0] > cand_dist:
						heappushpop(candidate_dists, (- cand_dist, cand))
			
			# Pick off first elements (the actual words) and return them
			# ordered largest ("least negative") to smallest
			return [x[1] for x in reversed(candidate_dists)]

	def initial_filter(self, word, delta = 3):
		'''
		Given <word>, produce a set of possible corrections all with length
		+/- <delta> of <word> by indexing based on <word>'s first letter and
		length. See above description of self.letter_and_length_dictionary for 
		more information
		'''
		first_letter = word[0]
		word_length = len(word)
		min_length_to_check = min(1, word_length - delta)
		max_length_to_check = word_length + delta
		candidates = set()

		for acceptable_length in range(min_length_to_check, max_length_to_check + 1):

			# Check if there exists a word of length <acceptable_length> that starts with <first_letter>
			if first_letter in self.letter_and_length_dictionary:
				if acceptable_length in self.letter_and_length_dictionary[first_letter]:
					candidates.update(self.letter_and_length_dictionary[first_letter][acceptable_length])
			else:
				candidates = []
				print 'No words in our dictionary start with "%s"' % first_letter

		return candidates 

	def check_line(self, line):
		'''
		Return <line> with any spelling corrections the user chooses from our algorithm's 
		suggestions
		'''
		tokens = wordpunct_tokenize(line)
		corrected_line = line

		for word in tokens:
			stripped_word = word.lower().strip()

			# Don't try to correct words that don't contain any letters
			if len(stripped_word) != 0 and re.search(r'[A-Za-z]', word) != None:
				# Check both the word and its stem
				if stripped_word not in self.dictionary and self.stemmer.stem(word) not in self.dictionary:
					initial_cands = self.initial_filter(stripped_word)
					if len(initial_cands) > 0:
						candidate_replacements = self.get_closest_words(stripped_word, initial_cands)

						# If misspelled, user selects one of the closest (by edit_distance) replacements
						corrected_word = self.io.get_replacement_from_user(line, word, candidate_replacements)
						# Replacement first occurence of <word> in <line> with <corrected_word>
						corrected_line = corrected_line.replace(word, corrected_word, 1)
					else:
						print 'No suggestions found for "%s"' % word
					
		return corrected_line

	def write_new_file(self, edited_lines, infile_name):
		self.io.write_new_file(edited_lines, infile_name)
		

class CheckerIO:

	def get_replacement_from_user(self, line, word, cands):
		'''
		Displays <line> containing misspelled <word> and all <cands> as options 
		for replacements
		returns user's selection of replacement
		'''
		cands.insert(0, 'Keep current spelling')
		self.display_options(line, word, cands)
		replacement_index = raw_input('Enter your selection (number) from the above options:\n')

		try:
			index = int(replacement_index)
			# Option 0 displays 'Keep current spelling', but should return the actual
			# word if the user wants to keep old spelling
			replacement = word if index == 0 else cands[index]

		# Didn't enter a number
		except ValueError:
			print 'Couldn\'t parse your selection. Kept your current spelling.'
			replacement = word

		# Didn't pick a valid index
		except IndexError:
			print '%s was not an option. Kept your current spelling.' % replacement_index
			replacement = word

		print '-' * 20
		return replacement

	def display_options(self, line, word, cands):
		# Note that this can be problematic if the mispelled
		# word is a substring of a previous word in the line
		# being corrected
		# TODO fix this
		start_index = line.index(word)

		print '"%s" was misspelled on the following line:' % word
		# Put a caret underneath the start of the word
		# Note that long lines could cause the ^ to appear below another line 
		# of text
		print line.strip()
		print ' ' * start_index + '^'
		for i in range(len(cands)):
			print '%i: %s' % (i, cands[i])

	def get_lines_from_file(self, args):
		if len(args) == 2:
			file_name = args[1]
			try:
				with open(file_name, 'r') as f:
					all_lines = f.readlines()

			except IOError:
				print 'Unable to open %s' % file_name
				all_lines = None
			
		else:
			usage()
			all_lines = None
			file_name = None

		return all_lines, file_name


	def write_new_file(self, edited_lines, infile_name):
		outfile_name = 'corrected_' + infile_name
		f = open(outfile_name, 'w')
		for line in edited_lines:
			f.write(line)

		f.close() 
		print 'Wrote %s' % outfile_name

def edit_distance(s1, s2, insertion_cost = 1, deletion_cost = 1, sub_cost = 2):
	'''Calculate edit distance of transforming s1 to s2'''
	# Add '#' at start -- table will include a row/column for this character
	# Note that the actual strings start at index 1
	s1 = '#' + s1
	s2 = '#' + s2

	s1_length = len(s1)
	s2_length = len(s2)

	nrow = s1_length
	ncol = s2_length

	# Each entry is a row	
	distances = [[None] * ncol for x in range(nrow)]

	# First row distances
	for i in range(ncol):
		distances[0][i] = i

	# First column distances
	for i in range(nrow):
		distances[i][0] = i

	for row_num in range(1, nrow):
		for col_num in range(1, ncol):
			
			if s1[row_num] == s2[col_num]:
				# No replacement needed
				distances[row_num][col_num] = distances[row_num - 1][col_num - 1]
			else:
				del_candidate = distances[row_num - 1][col_num] + deletion_cost
				insert_candidate = distances[row_num][col_num - 1] + insertion_cost
				sub_candidate = distances[row_num - 1][col_num - 1] + sub_cost

				distances[row_num][col_num] = min(del_candidate, insert_candidate, sub_candidate)

	return distances[nrow - 1][ncol - 1]

def usage():
	print 'Usage: spell_checker.py <file_name>'

def main():
	sc = SpellChecker()
	io = CheckerIO()

	# Parses args, reads file, returns list of lines
	all_lines, infile = io.get_lines_from_file(sys.argv)
	
	if all_lines != None:
		revised_lines = []
		for line in all_lines:
			correct_line = sc.check_line(line)
			revised_lines.append(correct_line)
			
		io.write_new_file(revised_lines, infile)
		print ''.join(revised_lines)
	

if __name__ == '__main__':
	main()