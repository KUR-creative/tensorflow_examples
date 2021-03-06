# -*- coding: utf-8 -*-
# [Lab 10] 에서 사용된 소스코드 (DROP_OUT을 이용한 학습모델)
import input_data
import tensorflow as tf
import random

# 모델의 각 단계별 W(weight)에 랜덤하게 값을 초기화하기 위한 함수
def xaver_init(n_inputs, n_outputs, uniform = True):
    if uniform:
        init_range = tf.sqrt(6.0/ (n_inputs + n_outputs))
        return tf.random_uniform_initializer(-init_range, init_range)
    else:
        stddev = tf.sqrt(3.0 / (n_inputs + n_outputs))
        return tf.truncated_normal_initializer(stddev=stddev)

# 1) 데이터 및 변수 설정
learning_rate = 0.001
training_epochs = 15
batch_size = 100
display_step = 1

mnist = input_data.read_data_sets("MNIST_data/", one_hot=True)
checkpoint_dir = "cps/"

# tf Graph Input
x = tf.placeholder("float", [None, 784])  # mnist data image of shape 28*28=784 (흑백이므로 color를 위한 차원은 없음)
y = tf.placeholder("float", [None, 10])  # 0-9 digits recognition => 10 classes

# Create model
# Set model weights
# https://www.tensorflow.org/versions/master/how_tos/variable_scope/
# https://tensorflowkorea.gitbooks.io/tensorflow-kr/content/g3doc/how_tos/variable_scope/
# tf.get_variable(<name>, <shape>, <initializer>) 는 입력된 이름의 변수를 생성 또는 반환
#  - tf.Variable을 직접호출 대신 변수를 가져오거나 생성하는 데 사용 (여기서는 변수(W1, W2, W3)를 생성하는데 사용)
#  - 직접 가지고 오는 대신, 정의된 initializer를 통해 shape를 생성
W1 = tf.get_variable("W1", shape=[784,256], initializer=xaver_init(784, 256)) # "W1" 변수 생성,
W2 = tf.get_variable("W2", shape=[256, 256], initializer=xaver_init(256, 256))
W3 = tf.get_variable("W3", shape=[256, 128], initializer=xaver_init(256, 128))
W4 = tf.get_variable("W4", shape=[128, 128], initializer=xaver_init(128, 128))
W5 = tf.get_variable("W5", shape=[128, 10], initializer=xaver_init(128, 10))

b1 = tf.Variable(tf.zeros([256]))
b2 = tf.Variable(tf.zeros([256]))
b3 = tf.Variable(tf.zeros([128]))
b4 = tf.Variable(tf.zeros([128]))
b5 = tf.Variable(tf.zeros([10]))

# 2) Layer간 연결을 통해 최종 model 정의 (drop out을 이용하여 모델을 학습)
# Construct model
dropout_rate = tf.placeholder("float")

_L1 = tf.nn.relu(tf.add(tf.matmul(x, W1), b1))
L1  = tf.nn.dropout(_L1, dropout_rate)
_L2 = tf.nn.relu(tf.add(tf.matmul(L1, W2), b2))
L2  = tf.nn.dropout(_L2, dropout_rate)
_L3 = tf.nn.relu(tf.add(tf.matmul(L2, W3), b3))
L3  = tf.nn.dropout(_L3, dropout_rate)
_L4 = tf.nn.relu(tf.add(tf.matmul(L3, W4), b4))
L4  = tf.nn.dropout(_L4, dropout_rate)

activation = tf.add(tf.matmul(L4, W5), b5) # softmax를 사용하지 않는다.

# 3) Minimize error using cross entropy
#    softmax_cross_entropy_with_logits 함수 : activation 값을 softmax를 통하지 않은 숫자를 사용하는 함수
#    cross-entropy를 직접 구현한 예제 (https://github.com/freepsw/tensorflow_examples/blob/master/02.Study_TensorFlow/06%20-%20Save%20Learning/traning.py)
cost = tf.reduce_mean(tf.nn.softmax_cross_entropy_with_logits(activation, y))
#    AdamOptimizer 현존하는 알고리즘 중 가장 좋다고 함(강의에서)   --> 머가 좋은지 한번 확인 필요
optimizer = tf.train.AdamOptimizer(learning_rate=learning_rate).minimize(cost)  # Gradient Descent

# Initializing the variables
init = tf.global_variables_initializer()

# 4) 학습 실행 (Launch the graph)
with tf.Session() as sess:
    sess.run(init)
    # https://www.tensorflow.org/api_docs/python/state_ops/saving_and_restoring_variables#Saver
    # tensorflow에서 계산한 W(가중치 변수)를 특정 디렉토리에서 불러온다.
    # 만약 save된 W로 계산한 cost가 9.3이였다면, restore한 이후에 계산한 cost는 이보다 더 적어질 것이다.
    # (기존에 학습한 모델의 결과 활용)
    saver = tf.train.Saver()

    ckpt = tf.train.get_checkpoint_state(checkpoint_dir)
    if ckpt and ckpt.model_checkpoint_path:
        print ('load learning')
        saver.restore(sess, ckpt.model_checkpoint_path)

    # Training cycle
    for epoch in range(training_epochs):
        avg_cost = 0.
        # mnist.train.num_examples = 55000
        # batch_size = 100
        # total_batch = 550 ==> 1번의 epoch에 550개의 이미지를 학습한다
        total_batch = int(mnist.train.num_examples / batch_size)
        # Loop over all batches
        print "total batch : ", total_batch
        for i in range(total_batch):
            batch_xs, batch_ys = mnist.train.next_batch(batch_size)
            # Fit training using batch data
            sess.run(optimizer, feed_dict={x: batch_xs, y: batch_ys, dropout_rate: 0.7})
            # Compute average loss
            avg_cost += sess.run(cost, feed_dict={x: batch_xs, y: batch_ys, dropout_rate: 0.7}) / total_batch

        # Display logs per epoch step
        if epoch % display_step == 0:
            print ("Epoch:", '%04d' % (epoch + 1), "cost=", "{:.9f}".format(avg_cost))
    print ("Optimization Finished!")

    # Test model
    correct_prediction = tf.equal(tf.argmax(activation, 1), tf.argmax(y, 1))

    # Calculate accuracy
    accuracy = tf.reduce_mean(tf.cast(correct_prediction, "float"))
    print ("Accuracy:", accuracy.eval({x: mnist.test.images, y: mnist.test.labels, dropout_rate: 1}))

    #save_path = saver.save(sess, checkpoint_dir + 'model.ckpt')
    #print("Model saved in file: %s" % save_path)


    # 5) Test 데이터에서 임의로 1개의 이미지를 선택하여, 정답을 예측하는지 확인해보자.
    import matplotlib.pyplot as plt
    r = random.randint(0, mnist.test.num_examples -1) # 랜덤하게 1개 선택
    # 5-1) label에는 10개의 값을 가진 vector type이 저장되어 있음 [0, 1, 2, ...., 9] 각각의 확률값이 저장
    #      실제 값은 예를들면 [0.1, 0.5, 0.1 .... 0.0] ==> "1"의 확률값이 가장 높음 (index=1)
    print "Label : ", sess.run(tf.argmax(mnist.test.labels[r:r+1], 1)) # 실제 값을 출력 (정답)
    print "Predt : ", sess.run(tf.argmax(activation, 1), {x:mnist.test.images[r:r+1], dropout_rate:1}) # 모델이 예측한 값을 출력
    plt.imshow(mnist.test.images[r:r+1].reshape(28, 28), cmap="Greys", interpolation='nearest')
    plt.show()

# 출력 결과
# total batch :  550
# ('Epoch:', '0005', 'cost=', '0.000363186')
# [-0.01041649 -0.58344501 -0.06178524 -0.38875002  0.0670083   0.22043853
#  -0.25432891 -0.09421912  0.46506232  0.14277922]
# Optimization Finished!
# ('Accuracy:', 0.95679998)
# Model saved in file: cps/model.ckpt
# Label :  [4]
# Predt :  [4]
