from abc import ABC, abstractmethod

class model(ABC):


    @abstractmethod
    def predict(self):
        pass


    @abstractmethod
    def featureNormalization(self):
        pass

    
    @abstractmethod
    def addBias(self):
        pass
