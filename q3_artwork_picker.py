# -*- coding: utf-8 -*-
"""Q3_Artwork_Picker

Automatically generated by Colaboratory.
Author:Xiaomeng Yao

A dynamic art piece picking strategy:

The strategy is to pick up an art piece at the point where the remaining pieces will be of lower prices than the 
current one with a high probability. Since the art pieces are i.i.d distributed, there are only two factors affecting 
this probability. The first one is the probability that an arbitrary art piece's price is lower than the current piece's 
price, which positively affects the probability to be maximised. The second one is the number of pieces that haven't been 
seen yet, which negatively affects the probability that we want to maximise. Therefore, to maximise the probability, 
I consider a simple linear formula P(x>current_price)+1-P(x>current_price)/(no_remaining_pieces) > threshold. This left hand of 
this inequality can be interpreted as the probability that an arbitrary art piece's price is lower than the current 
penalised by the remaining sample size. Once the probability threshold has been reached, we terminate the process and pick up 
the current art piece. 

From here, we can see that there are two things yet to be worked out. The first one is the cumulative distribution of the art pieces, 
and the second one is the threshold value given the distribution.  To estimate the distribution, we simply sample half of the collected 
prices and apply a mixture Guassian distribution to estimate the unconditional non-parametric distribution
of the prices (An advanced version is to use a mixture density network to estimate the conditional non-parametric distribution
of the prices if additional information is available. For example, the location of the piece in the gallery.) 

Note: In practice, a mixture normal estimator with 12 components should be enough to estimate any given unconditional/conditional non-parametric 
distribution.

Having estimated the distribution, a simple grid search algo is utilized to choose the threshold that returns
the highest price in the second sample of the collected prices. 

Note the first 200 pieces are simply used for training and none of the first 200 pieces will be selected.  
As we collect more pieces, both the distribution of the artwork_strategy and the probability threshold will be recalculated 
to optimize the strategy's performance. 

An alternative strategy might be considering the formula 1-P^(no_remaining_pieces)(x<current_prices)  < threshold and using the 
similar method to work out P and the threshold value. 


Warning: this script has not been tested as the artwork API is not available.
"""

import numpy as np
import scipy 
import sklearn 
from scipy.stats import norm
from sklearn import mixture
from sklearn.model_selection import train_test_split

# import the imaginary API
import ART

# The artwork 
class artwork_strategy():
      def __init__(self, prices): 
        # threshold choices and the number of components for GMM can be customised. In fact,
        # 12 components should be enough to estimate any non-parametric distribution. 
        self.threshold=[0.5,0.6,0.7,0.8,0.9]
        self.components=2
        self.prices=prices
        self.train_1=None
        self.train_2=None
        self.GMM=None
        

      # Public members
      def prob_cal(self,price):
          """
          Calculate the cumulative probability that an arbitray future art piece's price
          will be lower than the given price, given the distribution has been captured 
          by a learnt mixture guassian distribution.

          """
          prob=0
          for i in range(self.components):
              # extract the weights and the distribution parameters for each mixed Guassian component
              weight=self.GMM.weights_[i]
              mu=self.GMM.means_[i][0]
              std=np.sqrt(self.GMM.covariances_[i][0][0])
              # calculate the cumulative probability by composing all the Guassian components
              prob=prob+weight*norm.cdf(price,loc=mu,scale=std)
        
          return prob

      def threshold_optim(self): 
           """
           Work out the threshold that picks up the piece of the highest price via a grid search. 
           """
           # initialisation
           self.__GMM_estimator()
           optim_price=self.train_2[0]
           optim_thresh=self.threshold[0]
           # grid search
           for i in range(len(self.threshold)):
             picked_price= self.__price_thres(self.threshold[i])
             if picked_price > optim_price:
              optim_price=picked_price
              optim_thresh = self.threshold[i]
           return (optim_thresh,optim_price)   



      #Private members
      def __price_thres(self,thres):
          """
          Given a probability threshold, pick up an art piece in the sample. 
          """
          for i in range(len(self.train_2)): 
              # The evaluation formula 
              if self.prob_cal(self.train_2[i])+(1-self.prob_cal(self.train_2[i]))/(len(self.train_2)-i)> thres:
                  keep_running=False
                  picked=self.train_2[i]
                  break   
          return picked


      def __split(self):
          """
          Split the historical prices. The first half is used to learn the distribution. The 
          second half of the sample is used to decide the threshold probability
          """
        # set shuffle as False for random selection.  
          self.train_1, self.train_2 = train_test_split(self.prices,test_size=0.5,shuffle=False)
          self.train_1=self.train_1.reshape(len(self.train_1),1)
     
      def __GMM_estimator(self):
          """
          Estimate the non-parametric distribution via mixed Guassian.
          """
          self.__split()
          self.GMM = mixture.GaussianMixture(n_components=self.components, covariance_type='full')
          self.GMM.fit(self.train_1)

def picker():
    """
     The main function to execute the dynamic strategy     
    """
    ## initialise the stack of historical prices 
    historical_prices =[]
    for i in range(1000):
      current_price=ART.get_next_artwork()
    # start considering picking up an art piece from the 200th art piece. 
      if i >200 and i <999:
        #update the distribtion and the threshold value as new information comes in
        strategy_updated=artwork_strategy(historical_prices)
        threshold_updated=strategy_updated.threshold_optimum()[1]
          # the evaluation formula: probability smaller than the current piece penalised by the number of remaining pieces
        if (strategy_updated.prob_cal(current_price)+(1-strategy_updated.prob_cal(current_price))/(1000-len(historical_prices)) > threshold_updated):
             ART.keep_current_work()
             break 
        else : historical_prices=historical_prices.append(current_price)
      elif i == 999:
        strategy_updated=artwork_strategy(historical_prices)
        if strategy_updated.prob_cal(current_price)> 0.5:
             ART.keep_current_work()
             break 
      else:   
        ART.keep_current_work()
        break

if __name__ == '__main__':
    picker()

# An attempt to implement mixture density network based strategy, which has not been completed yet

 """
import tensorflow as tf


from tensorflow_probability import distributions as tfd

from tensorflow.keras.layers import Input, Dense, Activation, Concatenate
from tensorflow.keras.callbacks import EarlyStopping, TensorBoard, ReduceLROnPlateau

class artwork_MDN_Strategy():
      def __init__(self, arg_cond,prices,Neurons,Components): 
        self.prices=prices
        self.arg_cond=arg_cond
        self.prices
        self.no_parameters =3
        self.components=3
        self.opt= tf.train.AdamOptimizer(1e-3)
        self.mon = EarlyStopping(monitor='val_loss', min_delta=0, patience=5, verbose=0, mode='auto')
        self.Neurons= Neurons
        self.Components=Components
      
      
      def train_mdn(self):
        self.mdn_sequential=self.__make_mdn_sequential(self.Neurons,self.Components)
        self.mdn_sequential.compile(loss=self.__gnll_loss, optimizer=self.opt)   
        self.mdn_sequential.fit(x=self.arg_cond, y=self.prices,epochs=1000, validation_split=0.35, 
                              callbacks=[self.mon]) 
    
     
          
     ## private members
        def __make_mdn_sequential(self,Neurons,Components):
   
        mdn_inputs = Input(shape=(self.arg_cond.shape[1],))
        h1 = Dense(self.Neurons, activation="relu")(mdn_inputs)
        h2 = Dense(self.Neurons, activation="relu")(h1)


        alphas = Dense(self.Components, activation="softmax", name="alphas")(h2)   # Create vector for alpha (softmax constrained)
        mus = Dense(self.Components, name="mus")(h2)                               # Create vector for mus
        sigmas = Dense(self.Components, activation="nnelu", name="sigmas")(h2)     # Create vector sigmas (nnelu constrained)
        mdn_outputs = Concatenate(name="output")([alphas, mus, sigmas])  
    
        mdn_sequential_1 = tf.keras.Model(inputs=mdn_inputs, outputs=mdn_outputs)
    
        return mdn_sequential_1

     def __nnelu(self,input):
         """ Computes the Non-Negative Exponential Linear Unit
         """
         return tf.add(tf.constant(1, dtype=tf.float32), tf.nn.elu(input))

    def __slice_parameter_vectors(self,parameter_vector):
        """ Returns an unpacked list of paramter vectors.
        """
        return [parameter_vector[:,i*components:(i+1)*components] for i in range(no_parameters)]

    def __gnll_loss(self,y, parameter_vector):
        """ Computes the mean negative log-likelihood loss of y given the mixture parameters.
        """
        alpha, mu, sigma = slice_parameter_vectors(parameter_vector) # Unpack parameter vectors
    
        gm = tfd.MixtureSameFamily(
        mixture_distribution=tfd.Categorical(probs=alpha),
        components_distribution=tfd.Normal(
            loc=mu,       
            scale=sigma))
    
        log_likelihood = gm.log_prob(tf.transpose(y)) # Evaluate log-probability of y
    
        return -tf.reduce_mean(log_likelihood, axis=-1)
"""

