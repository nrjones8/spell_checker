# Nick Jones

import re
from heapq import heappush, heappushpop

class SpellChecker:

	def __init__(self, dict_location = '/usr/share/dict/words'):
		# Read in dictionary, strip newlines from each word
		self.dictionary = self.get_dictionary(dict_location)
		self.letter_and_length_dictionary = self.preprocess_dictionary(self.dictionary)
		self.io = CheckerIO()

	def get_dictionary(self, dict_location):
		return set([w.strip() for w in file(dict_location).readlines()])

	def preprocess_dictionary(self, full_dict):
		# 'a' => {4 => set(<4 letter words starting with 'a'>), 5 => set()} etc.
		first_letter_to_length_words = {}
		for word in full_dict:
			word_len = len(word)
			first_letter_to_length_words.setdefault(word[0], {})
			first_letter_to_length_words[word[0]].setdefault(word_len, set()).add(word)

		return first_letter_to_length_words

	def get_closest_words(self, word, k = 5):
		'''
		Returns <word> if <word> is in self.dictionary, or the closest <k>
		words measured by the <edit_distance> function
		'''
		if word in self.dictionary:
			return word
		else:
			# TODO check if there aren't <k> candidates
			all_candidate_words = self.initial_filter(word)
			
			# Each entry (word, distance)
			candidate_dists = []
			# Could use a heap here instead
			for cand in all_candidate_words:
				cand_dist = edit_distance(word, cand)
				if len(candidate_dists) < k:
					heappush(candidate_dists, (- cand_dist, cand))
				else:
					# "peek" at largest distance element, discard it if larger than 
					# cand_dist
					if candidate_dists[0] > cand_dist:
						heappushpop(candidate_dists, (- cand_dist, cand))
			
			# Pick off first elements (the actual words)	
			return [x[1] for x in reversed(candidate_dists)]

	def initial_filter(self, word, delta = 3):
		'''
		Given <word>, produce a set of possible corrections all with length
		+/- <delta> of <word>
		'''
		first_letter = word[0]
		word_length = len(word)
		min_length_to_check = min(1, word_length - delta)
		max_length_to_check = word_length + delta
		candidates = set()

		for acceptable_length in range(min_length_to_check, max_length_to_check + 1):
			# Check if there exists a word of length <acceptable_length> that starts with <first_letter>
			if acceptable_length in self.letter_and_length_dictionary[first_letter]:
				candidates.update(self.letter_and_length_dictionary[first_letter][acceptable_length])

		return candidates 

	def check_line(self, line):
		tokens = tokenize(line)
		corrected_tokens = tokens
		corrected_line = line

		for i in range(len(tokens)):
			word = tokens[i]

			if len(word) != 0:
				candidate_replacements = self.get_closest_words(word)
				if candidate_replacements != word:
					# If misspelled, user selects one of the closest (by edit_distance) replacements
					corrected_word = self.io.get_replacement_from_user(line, word, candidate_replacements)
					# Replacement first occurence of <word> in <line> with <corrected_word>
					corrected_line = corrected_line.replace(word, corrected_word, 1)
					corrected_tokens[i] = corrected_word
					
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
		self.display_options(line, word, cands)
		replacement_index = raw_input('Enter your selection (number) from the above options:\n')

		try:
			index = int(replacement_index)
			replacement = cands[index]

		except ValueError:
			print 'Couldn\'t parse your selection. Default (option 0) was used'
			replacement = cands[0]

		except IndexError:
			print '%s was not an option. Default (option 0) was used' % replacement_index
			replacement = cands[0]

		print '-' * 20
		return replacement

	def display_options(self, line, word, cands):
		start_index = line.index(word)

		print '"%s" was misspelled on the following line:' % word
		print line.strip()
		print ' ' * start_index + '^'
		for i in range(len(cands)):
			print '%i: %s' % (i, cands[i])

	def write_new_file(self, edited_lines, infile_name):
		outfile_name = 'corrected_' + infile_name
		f = open(outfile_name, 'w')
		for line in edited_lines:
			f.write(line)

		f.close() 
		print 'Wrote %s' % outfile_name

def tokenize(text):
	return re.split(r'\s+', text)


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

def main():
	sc = SpellChecker()
	infile = 'test_text.txt'
	
	all_lines = file(infile).readlines()
	revised_lines = []
	for line in all_lines:
		correct_line = sc.check_line(line)
		revised_lines.append(correct_line)
		# print 'Had tokens', tokenize(line)
		# print 'Now has', correct_line
	sc.write_new_file(revised_lines, infile)
	print ''.join(revised_lines)
	

if __name__ == '__main__':
	main()