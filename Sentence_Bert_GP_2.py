from sentence_transformers import InputExample
from torch.utils.data import DataLoader
import math
from sentence_transformers import LoggingHandler, util
from sentence_transformers.cross_encoder import CrossEncoder
from sentence_transformers.cross_encoder.evaluation import CESoftmaxAccuracyEvaluator
from sentence_transformers.readers import InputExample
from sentence_transformers import SentenceTransformer,  util, LoggingHandler, InputExample
from sentence_transformers.cross_encoder.evaluation import CEBinaryClassificationEvaluator
import logging
from datetime import datetime
from sklearn.model_selection import KFold
from sklearn.model_selection import RepeatedKFold
from sklearn.linear_model import LogisticRegression
from sentence_transformers import SentenceTransformer, util
import itertools
from pandas import DataFrame
import pandas as pd
import numpy as np
import sys
from sklearn.metrics import precision_recall_fscore_support


if __name__ == '__main__':
	annots = []
	randSent = []
	comb = []
	lis = []
	labels = []

	with open('CombinedAnnots.txt', 'r', encoding="utf8") as f:
		for line in f:
			annots.append(line)

	with open('RandomSentences.txt', 'r', encoding="utf8") as f:
		for line in f:
			randSent.append(line)

	comb = annots + randSent

	combinations = list(itertools.combinations(comb, 2))
	for com in combinations:
		if (com[0] and com[1]) in (annots or randSent):
			lis.append('entailment')
		else: 
			lis.append('contradiction')

	#print(combinations[0])
	# print(lis[52:70])
	# print(len(combinations))

	test = list(zip(combinations, lis))
		
	for comb, li in zip(combinations, lis):
		join = comb + tuple(map(str, li.split(', ')))
		labels.append(join)

	#print(labels[0])
	#df = DataFrame (labels, columns=['Sentence1', 'Sentence2', 'Label'])
	df = DataFrame (test, columns=['Sentences', 'Label'])
	pd.options.display.max_colwidth = 500
	#print(df)

	logging.basicConfig(format='%(asctime)s - %(message)s',
					datefmt='%Y-%m-%d %H:%M:%S',
					level=logging.INFO,
					handlers=[LoggingHandler()])
	logger = logging.getLogger(__name__)

	kf10 = KFold(n_splits=10, shuffle=False)
	i = 0
	for train_index, test_index in kf10.split(df):
		X_train = df.iloc[train_index].loc[:, 'Sentences']
		X_test = df.iloc[test_index]['Sentences']
		y_train = df.iloc[train_index].loc[:,'Label']
		y_test = df.loc[test_index]['Label']

		label2int = {"contradiction": 0, "entailment": 1, "neutral": 2}

		train_samples = []
		for x, y in zip(X_train, y_train):
			label_id = label2int[y]
			train_samples.append(InputExample(texts=[x[0], x[1]], label=label_id))

		# for train in train_samples[:5]:
		#   print(train)

		# train_samples = [
		#   InputExample(texts=['sentence1', 'sentence2'], label=label2int['neutral']),
		#   InputExample(texts=['Another', 'pair'], label=label2int['entailment']),
		# ]

		#test_samples = []
		#for x, y in zip(X_test, y_test):
		#  label_id = label2int[y]
		# test_samples.append(InputExample(texts=[x[0], x[1]], label=label_id))

		#test_samples = []
		#test_samples = [list(x) for x in zip(X_test, y_test)]
		#print(test_samples[:5])
		# for x, y in zip(X_test, y_test):
		#   test_samples.append(InputExample(texts=[x[0], x[1]], label=label_id))

		#for test in test_samples[:5]:
		# if all(isinstance(i, list) for i in test_samples):
		# 	print("True")

		train_batch_size = 16
		num_epochs = 4
		model_save_path = 'output/training_allnli-'+datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

		#Define our CrossEncoder model. We use distilroberta-base as basis and setup it up to predict 3 labels
		#model = CrossEncoder('distilroberta-base', num_labels=len(label2int))
		model = CrossEncoder('bert-base-cased', num_labels=1)

		#We wrap train_samples, which is a list ot InputExample, in a pytorch DataLoader
		train_dataloader = DataLoader(train_samples, shuffle=True, batch_size=train_batch_size)

		#During training, we use CESoftmaxAccuracyEvaluator to measure the accuracy on the dev set.
		#evaluator = CESoftmaxAccuracyEvaluator.from_input_examples(test_samples, name='AllNLI-dev')
		#evaluator = CESoftmaxAccuracyEvaluator.from_input_examples(test_samples, name='test')
		#evaluator = CEBinaryClassificationEvaluator.from_input_examples(test_samples, name='test')

		warmup_steps = math.ceil(len(train_dataloader) * num_epochs * 0.1) #10% of train data for warm-up
		logger.info("Warmup-steps: {}".format(warmup_steps))

		model.fit(train_dataloader=train_dataloader,
					#evaluator=evaluator,
					epochs=num_epochs,
					evaluation_steps=10000,
					warmup_steps=warmup_steps,
					output_path=model_save_path)
		
		
		test_samples = []
		scores_test = []
		for x, y in zip(X_test, y_test):
			label_id = label2int[y]
			test_samples.append([x[0], x[1]])
			scores_test.append(label_id)

		# for score in scores_test:
		# 	if score[0].find('contradiction'):
		# 		score[0].replace('contradiction', '0')
		# 	if score[0].find('entailment'):
		# 		score[0].replace('entailment', '1')
		# 	if score[1].find('contradiction'):
		# 		score[1].replace('contradiction', '0')
		# 	if score[1].find('entailment'):
		# 		score[1].replace('entailment', '1')

		scores = model.predict(test_samples, batch_size=train_batch_size)
		#print(scores.size)

		score_class = []
		scores_binary = []
		for score in scores:
			if score < 0.5:
				score_class.append(str(score) + ' - ' + 'contradiction')
				scores_binary.append(0)
			elif score >= 0.5:
				score_class.append(str(score) + ' - ' + 'entailment')
				scores_binary.append(1)
		
		print(len(scores_binary))
		print(scores_test)
		print(len(scores_binary))
		print(scores_test)
		# test_binary = []
		# for test in test_samples:
		# 	if test[0] < 0.5:
		# 		test_binary.append('0')
		# 	if test[0] >= 0.5:
		# 		test_binary.append('1')
		# 	if test[1] < 0.5:
		# 		test_binary.append('0')
		# 	if test[1] >= 0.5:
		# 		test_binary.append('1')

		y_true = np.array(scores_test)
		y_pred = np.array(scores_binary)
		
		print(precision_recall_fscore_support(y_true, y_pred, average=None, labels=[0, 1]))

		print(precision_recall_fscore_support(y_true, y_pred, average='macro'))
		print(precision_recall_fscore_support(y_true, y_pred, average='micro'))
		print(precision_recall_fscore_support(y_true, y_pred, average='weighted'))

		#model = CrossEncoder('distilroberta-base', num_labels=2)
		#model = LogisticRegression(solver="liblinear", multi_class="auto")
		#model = SentenceTransformer('nq-distilbert-base-v1')





		#Train the model
		# model.fit(X_train, y_train) #Training the model
		# query_embedding = model.encode(X_train)
		# passage_embedding = model.encode(y_train)
		# print("Similarity:", util.pytorch_cos_sim(query_embedding, passage_embedding))
		# print(f"Accuracy for the fold no. {i} on the test set: {accuracy_score(y_test, model.predict(X_test))}")
