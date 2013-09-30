# Nick Jones

import re

class SpellChecker:

	def __init__(self, dict_location = '/usr/share/dict/words'):
		# Read in dictionary, strip newlines from each word
		self.dictionary = self.get_dictionary(dict_location)
		self.letter_and_length_dictionary = self.preprocess_dictionary(self.dictionary)

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

	def correct_spelling(self, word):
		'''
		Returns <word> if <word> is in self.dictionary, or the closest
		correct word measured by the <edit_distance> function
		'''
		if word in self.dictionary:
			return word
		else:

			candidate_words = self.initial_filter(word)
			min_dist, min_word = None, None
			for cand in candidate_words:
				cand_dist = edit_distance(word, cand)

				if min_dist == None or cand_dist < min_dist:
					min_dist = cand_dist
					min_word = cand

			print 'off by %i' % min_dist

			return min_word

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

		for acceptable_length in range(min_length_to_check, max_length_to_check):
			# Check if there exists a word of length <acceptable_length> that starts with <first_letter>
			if acceptable_length in self.letter_and_length_dictionary[first_letter]:
				candidates.update(self.letter_and_length_dictionary[first_letter][acceptable_length])

		return candidates 

	def check(self, document):
		for word in document:
			replacement = self.correct_spelling(word)
			if replacement != word:
				print 'Replaced %s with %s' % (word, replacement)


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
	text = file('test_text.txt').read()
	tokens = tokenize(text)
	print tokens
	sc = SpellChecker()
	sc.check(tokens)

if __name__ == '__main__':
	main()