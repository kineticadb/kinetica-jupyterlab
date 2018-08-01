import uuid
from tensorflow.python.ops import array_ops
import tensorflow as tf

# define variational autoencoder
class cvae(object):
    def __init__(self, learning_rate, batch_size, num_drugs, **kwargs):
        self.learning_rate = learning_rate
        self.batch_size = batch_size
        self.num_drugs = num_drugs
        self.config = tf.ConfigProto()
        self.graph1 = tf.Graph()
        
        with self.graph1.as_default():
            self.prob = tf.placeholder_with_default(0.2, shape=())
            self.x = tf.placeholder(shape=[None, num_drugs], dtype=tf.float32, name="input")
            
            self.encoder = tf.layers.dense(self.x, num_drugs//10, 
                                      activation=tf.nn.selu, 
                                      kernel_regularizer=tf.contrib.layers.l2_regularizer(scale=0.001),
                                      kernel_initializer=tf.truncated_normal_initializer(mean=0, stddev=0.05, seed=13))
            
            self.nn = tf.layers.dropout(inputs=self.encoder, rate=self.prob, name = "encoded1")

            sd = 0.00005 * tf.layers.dense(self.x, units=num_drugs//10)            
            epsilon = 0.005 * tf.random_normal(tf.stack([tf.shape(self.nn)[0], num_drugs//10])) 
            self.z  = self.nn + 0.05 * tf.multiply(epsilon, tf.exp(sd))

            decoder = tf.layers.dense(self.z, 
                                      num_drugs, 
                                      #activation=tf.nn.selu, 
                                      kernel_regularizer=tf.contrib.layers.l2_regularizer(scale=0.001),
                                      kernel_initializer=tf.truncated_normal_initializer(mean=0, stddev=0.05, seed=13))
            
            self.pred = tf.nn.selu(decoder, name= "output")  
            ###############################################################
            self.topK = tf.nn.top_k(self.pred, self.num_drugs//2, sorted=True)
            #minima = topK[self.num_drugs//10]
            self.pred = tf.nn.relu(tf.add(self.pred, -self.topK[0][:,-1:]))
            ###############################################################
            l2_loss = tf.losses.get_regularization_loss()
            latent_loss = -0.0005 * tf.reduce_mean(1.0 + 2.0 * sd - tf.square(self.nn) - tf.exp(2.0 * sd), 1)
            
            #self.loss = tf.reduce_mean(tf.reduce_mean((self.pred - self.x)**2,1)+latent_loss)
            #self.loss += l2_loss 
            self.loss = tf.reduce_mean((self.pred - self.x)**2)+0.005*l2_loss
            
            self.optimizer = tf.train.AdamOptimizer(learning_rate, 
                                               beta1=0.9, beta2=0.999, 
                                               epsilon=1e-08, 
                                               use_locking=False).minimize(self.loss)
            
            tf.summary.scalar("loss", self.loss)
            self.merged_summary_op = tf.summary.merge_all()
            self.init = tf.global_variables_initializer()
    def train(self, data, epoch = 5):
        self.config.gpu_options.allow_growth = True
        self.sess = tf.Session(graph = self.graph1, config=self.config)
        self.sess.run(self.init)
        for epoch in range(epoch):
            for step in range(len(data)//self.batch_size):
                x_vals = data[step * self.batch_size: step * self.batch_size + self.batch_size , :]
                predt, _, val, summary = self.sess.run([self.pred, self.optimizer, self.loss, self.merged_summary_op],
                                                  feed_dict={self.x: x_vals})
            print("epoch: {}, value: {}".format(epoch, val))
    def infer(self, data):
        resMat = self.sess.run([self.pred],feed_dict={self.x: data, self.prob: 0})
        resMat=resMat[0]
        return resMat
    
    def encodeInfer(self, data):
        resMat = self.sess.run([self.z],feed_dict={self.x: data, self.prob: 0})
        resMat=resMat[0]
        return resMat
    
    def decodeInfer(self, data):
        resMat = self.sess.run([self.pred],feed_dict={self.z: data, self.prob: 0})
        resMat=resMat[0]
        return resMat
        
# define autoencoder
class AutoEnc(object):
    def __init__(self, learning_rate, batch_size, num_drugs, **kwargs):
        self.learning_rate = learning_rate
        self.batch_size = batch_size
        self.num_drugs = num_drugs
        self.config = tf.ConfigProto()
        self.graph1 = tf.Graph()
        if "hidden_dim" not in kwargs.keys():
            hidden_dim = num_drugs//15
        else:
            hidden_dim = int(kwargs["hidden_dim"])
        with self.graph1.as_default():
            
            self.prob = tf.placeholder_with_default(0.2, shape=())
            self.x = tf.placeholder(shape=[None, num_drugs], dtype=tf.float32, name="input")
        #     y = tf.placeholder(shape=[None, num_drugs], dtype=tf.float32, name="output")
            encoder = tf.layers.dense(self.x, hidden_dim, 
                                      activation=tf.nn.selu,  
                                  kernel_regularizer=tf.contrib.layers.l2_regularizer(scale=0.001),
                                      kernel_initializer=tf.truncated_normal_initializer(mean=0, stddev=0.05),
                                      bias_initializer=tf.truncated_normal_initializer(mean=0, stddev=0.01))
            #encoder = tf.nn.batch_normalization(encoder, 0, 0.05, 0,1 , 0.01)
            self.nn1 = tf.layers.dropout(inputs=encoder, rate=self.prob, name = "encoded1")


            
            if kwargs["doubled"] == True:
                nn = tf.layers.dense(self.nn1, 
                                     num_drugs//15, 
                                     activation=tf.nn.selu, 
                                     kernel_regularizer=tf.contrib.layers.l2_regularizer(scale=0.01),
                                     kernel_initializer=tf.truncated_normal_initializer(mean=0, stddev=0.05),
                                     bias_initializer=tf.truncated_normal_initializer(mean=0, stddev=0.1))
                self.nn2 = tf.layers.dropout(inputs=nn, rate=self.prob, name = "encoded2")
                nn = tf.layers.dense(self.nn2, 
                                     num_drugs//15, 
                                     activation=tf.nn.selu, 
                                     kernel_regularizer=tf.contrib.layers.l2_regularizer(scale=0.01),
                                     kernel_initializer=tf.truncated_normal_initializer(mean=0, stddev=0.05),
                                     bias_initializer=tf.truncated_normal_initializer(mean=0, stddev=0.1))
                self.nn1 = tf.layers.dropout(inputs=nn, rate=self.prob)

            decoder = tf.layers.dense(self.nn1, 
                                      num_drugs, 
                                      #activation=tf.identity, 
                                      #activation=tf.nn.relu,
                                      kernel_regularizer=tf.contrib.layers.l2_regularizer(scale=0.01),
                                      kernel_initializer=tf.truncated_normal_initializer(mean=0, stddev=0.05),
                                      bias_initializer=tf.truncated_normal_initializer(mean=0, stddev=0.01))

            self.pred = tf.nn.selu(decoder, name= "output")
            self.topK = tf.nn.top_k(self.pred, self.num_drugs//2, sorted=True)
            self.pred = tf.nn.relu(tf.add(self.pred, -self.topK[0][:,-1:]))
            l2_loss = tf.losses.get_regularization_loss()
            self.loss = tf.reduce_mean((self.pred - self.x)**2)+0.005*l2_loss
            self.optimizer = tf.train.AdamOptimizer(learning_rate, 
                                               beta1=0.9, beta2=0.999, 
                                               epsilon=1e-08, 
                                               use_locking=False).minimize(self.loss)
            tf.summary.scalar("loss", self.loss)
            self.merged_summary_op = tf.summary.merge_all()
            self.init = tf.global_variables_initializer()
            
    def train(self, data, epoch = 5):
        self.config.gpu_options.allow_growth = True
        self.sess = tf.Session(graph = self.graph1, config=self.config)
        self.sess.run(self.init)
        for epoch in range(epoch):
            for step in range(len(data)//self.batch_size):
                x_vals = data[step * self.batch_size: step * self.batch_size + self.batch_size , :]
                predt, _, val, summary = self.sess.run([self.pred, self.optimizer, self.loss, self.merged_summary_op],
                                                  feed_dict={self.x: x_vals})
            print("epoch: {}, loss: {}".format(epoch, val))
        return val
            
    def infer(self, data):
        resMat = self.sess.run([self.pred],feed_dict={self.x: data, self.prob: 0})
        resMat=resMat[0]
        return resMat
    
    def encodeInfer(self, data):        
        resMat = self.sess.run([self.nn1],feed_dict={self.x: data, self.prob: 0})
        resMat=resMat[0]
        return resMat
    
    def decodeInfer(self, data):
        resMat = self.sess.run([self.pred],feed_dict={self.nn1: data, self.prob: 0})
        resMat=resMat[0]
        return resMat