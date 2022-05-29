from benchopt import BaseDataset
from benchopt import safe_import_context

with safe_import_context() as import_ctx:
    import numpy as np
    from scipy.sparse import rand as sprand
    from scipy.sparse.linalg import LinearOperator


class Dataset(BaseDataset):

    name = "Simulated"

    # List of parameters to generate the datasets. The benchmark will consider
    # the cross product for each key in the dictionary.
    parameters = {
        'n_samples': [400],
        'n_features': [250],
        'n_blocks': [10],
        'mu': [0],
        'sigma': [0.1],
        'type_A': ['identity', 'random', 'conv'],
        'type_x': ['block', 'sin'],
        'random_state': [27]
    }

    def __init__(self, n_samples=5, n_features=5, n_blocks=1,
                 mu=0, sigma=0.01, type_A='identity', type_x='block',
                 random_state=27):
        # Store the parameters of the dataset
        self.n_samples, self.n_features = n_samples, n_features
        self.n_blocks = n_blocks
        self.mu, self.sigma = mu, sigma
        self.type_A, self.type_x = type_A, type_x
        self.random_state = random_state

    def skip(self):
        if ((self.type_A == 'identity' or self.type_A == 'random')
           and self.n_samples != self.n_features) \
           or (self.type_A == 'conv' and self.n_samples - self.n_features < 1):
            return True, \
                   "samples and features number don't match with type of A"
        return False, None

    def get_A(self, rng):
        if self.type_A == 'identity':
            A = LinearOperator(
                dtype=np.float64,
                matvec=lambda x: x,
                matmat=lambda X: X,
                rmatvec=lambda x: x,
                rmatmat=lambda X: X,
                shape=(self.n_samples, self.n_features),
            )
        elif self.type_A == 'random':
            filt = rng.randn(self.n_samples, self.n_features)
            A = LinearOperator(
                dtype=np.float64,
                matvec=lambda x: filt @ x,
                matmat=lambda X: filt @ X,
                rmatvec=lambda x: filt.T @ x,
                rmatmat=lambda X: filt.T @ X,
                shape=(self.n_samples, self.n_features),
            )
        elif self.type_A == 'conv':
            len_A = self.n_samples - self.n_features + 1
            filt = rng.randn(len_A)
            A = LinearOperator(
                dtype=np.float64,
                matvec=lambda x: np.convolve(x, filt, mode='full'),
                matmat=lambda X: np.array(
                    [np.convolve(x, filt, mode='full') for x in X.T]
                ).T,
                rmatvec=lambda x: np.correlate(x, filt, mode='valid'),
                rmatmat=lambda X: np.array(
                    [np.correlate(x, filt, mode='valid') for x in X.T]
                ).T,
                shape=(self.n_samples, self.n_features)
            )
        return A

    def get_data(self):
        rng = np.random.RandomState(self.random_state)
        if self.type_x == 'sin':
            # A * cos + noise ~ N(mu, sigma)
            t = np.arange(self.n_features)
            x = np.cos(np.pi*t/self.n_features * self.n_blocks)
        else:
            # A * blocked signal + noise ~ N(mu, sigma)
            z = sprand(
                1, self.n_features, density=self.n_blocks/self.n_features,
                random_state=rng
            ).toarray()[0]
            x = np.cumsum(rng.randn(self.n_features) * z)
        A = self.get_A(rng)
        y = A @ x + rng.normal(self.mu, self.sigma, self.n_samples)
        data = dict(A=A, y=y, x=x)

        return data
