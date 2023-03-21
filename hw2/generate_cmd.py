# Z ping Z       5 
# show_table X   1
# show_table Y   1
# clear X        3
import random

X = ['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'h7', 'h8', 's1', 's2', 's3', 's4', 's5', 's6', 's7']
Y = ['all_switches', 'all_hosts']
Z = ['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'h7', 'h8']
for i in range(5):
	for i in range(4):
		if i == 2:
			print('show_table', X[random.randint(0,14)])
		num = random.random()
		if num < 0.7:
			random.shuffle(Z)
			print(Z[0], 'ping', Z[1])
		else:
			print('clear', X[random.randint(0, 14)])
	print('show_table all_switches')
	print('show_table all_hosts')
print('exit')
