from .model import model
import numpy as np
from typing import Tuple, Optional
from tqdm import tqdm
import matplotlib.pyplot as plt

class XGmodel(model):
    def __init__(self, lr: float = 0.01, num_iters: int = 100,
                 random_init_weight: bool = True, normalize_data: bool = True,
                 regularization: bool = False, Lambda: int = 1, reduce_dimension: bool = False,
                 reduction_size: int = Optional[int]):
        super().__init__()
        self.lr = lr
        self.num_iters = num_iters            
        self.random_init_weight = random_init_weight
        self.normalize_data = normalize_data
        self.regularization = regularization
        self.Lambda = Lambda
        self.reduce_dimension = reduce_dimension
        self.reduction_size = reduction_size

    def fit(self, X, Y, show=False):


        if self.normalize_data or self.reduce_dimension:
            X = self.featureNormalization(X)

        if self.reduce_dimension:
            X, total_variance = self.PCA(X, self.reduction_size)
            print(f"Roughly {round(total_variance*100, 2)}% of the total variation in the dataset was captured.")


        X = self.addBias(X)
        C_history = []
        m = X.shape[1]
        
        if self.random_init_weight:
            self.w = np.random.rand(m, 1)
        else:
            self.w = np.zeros((m, 1))
        pbar = tqdm(range(self.num_iters))

        for i in pbar:
            new_w = np.zeros(X.shape)

            C, grad = self.costFunction(self.w, X, Y)
            C_history.append(C)
            new_w = self.w - self.lr*grad
            self.w = new_w.copy()
            pbar.set_description(f"Loss: {round(C, 2)}")

        if show:
            plt.plot(C_history)
            plt.xlabel("Num iteration")
            plt.ylabel("Loss")
            plt.show()


    def predict(self, X: np.ndarray) -> Tuple[int, np.ndarray]:
        
        if self.normalize_data or self.reduce_dimension:
            if not hasattr(self, "mean") or not hasattr(self, "std") or not hasattr(self, "w"):
                raise RuntimeError("Model must be trained before prediction")
            X = (X - self.mean) / self.std
        
        if self.reduce_dimension:
            X, total_variance = self.PCA(X, self.reduction_size)

        X = self.addBias(X)
        probs = self._sigmoid(X @ self.w)
        preds = (probs >= 0.5).astype(int)

        
        return preds, probs
            



    def featureNormalization(self, X: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        

        self.mean = np.mean(X, axis=0)
        self.std = np.std(X, axis=0,ddof=1)
        X_norm = (X-self.mean)/self.std

        return X_norm


    def  addBias(self, X):
        
        Bias = np.ones((X.shape[0], 1))
        X_extended = np.column_stack((Bias, X))

        return X_extended
    
    def costFunction(self, w: np.ndarray, X: np.ndarray, Y:np.ndarray):
        
        m = X.shape[0]
        h = self._sigmoid(X@w)
        Y = Y.reshape(-1, 1)

        if self.regularization:
            w1 = np.vstack((np.array([0]),w[1:,:])) # set the BIAS corresponding weights to
            p = self.Lambda*(w1.transpose() @ w1)/(2*m) # penalization
            C = (1/m)*np.sum((-Y)*np.log(h)-((1-Y)*np.log(1-h))) + p
            grad = (X.transpose() @ (h -Y) + self.Lambda*w1)/m
        else:      
            C = (1/m)*np.sum((-Y)*np.log(h)-((1-Y)*np.log(1-h)))
            grad = (X.transpose())@(h-Y)/m
        
        return C, grad


    def _sigmoid(self, z):
        g = 1/(1+np.exp(-z))
        return g
    

    def PCA(self, X, reduction_size: int = 2) -> np.ndarray:
        
        X = self.featureNormalization(X)
        covariance_matrix = np.cov(X, ddof=1, rowvar=False)
        eigenvalues, eigenvectors = np.linalg.eig(covariance_matrix)
        order_of_importance = np.argsort(eigenvalues)[::-1]

        sorted_eigenvalues = eigenvalues[order_of_importance]
        sorted_eigenvectors = eigenvectors[:, order_of_importance]

        explained_variance = sorted_eigenvalues / np.sum(sorted_eigenvalues)

        X = np.matmul(X,sorted_eigenvectors[:, :reduction_size])


        total_explained_variance = sum(explained_variance[:reduction_size]) 

        return X, total_explained_variance
