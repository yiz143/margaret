#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import numpy as np
import matplotlib.pyplot as plt
import sklearn.metrics

class RegressionAnalyzer:
    """
Analyzer(prediction, truth, scale_func)

This class can calculate the bias, spread, and outlier fraction,
given an array of predicted values vs. truths. The procedure is
as follows:

Step 1: Choose a function f over which to model the scaling of the residual
    - Let res = (y_prediction - y_truth) / f(y_truth)
    - e.g., typically in the case of photo-z error, f(x) = 1 + x so that
        res = (z_predict - z_true) / (1 + z_true)
    
Step 2: Define this function, f
    - Ensure that f_inv(f(x)) == x
    - e.g., for photo-z
        - ``def f(z): return 1 + z``

Step 3: Choose an estimator of the spread of the residual
    - Standard Deviation: np.std(res, ddof=1)
    - Normalized Median Absolute Deviation: 1.48 * np.median(np.abs(res))

Step 4: Plot the residuals vs. the true value


Usage Example for Redshift Analysis
===================================

>>> # Create regressor object and calculate prediction/truth values
>>> z_predict, z_true = regressor.RFregressor()
>>> 
>>> f = lambda z: z + 1  # optional
>>> 
>>> analysis = MLAnalysis.RegressionAnalyzer(z_predict, z_true, scale_as=f)
>>> # Several scoring metrics can be accessed via:
>>> #           - analysis.r2()
>>> #           - analysis.nmad()
>>> #           - analysis.std()
>>> #           - analysis.outlier_frac()
>>> 
>>> target_label = "z"  # optional
>>> f_label = lambda target: f"(1 + {target})"  # optional
>>> 
>>> analysis.plot_residuals(target_label=target_label, f_label=f_label,
                            outlier_sigmas=3, spread_estimator="nmad")
>>> plt.show()
    """
    def __init__(self, prediction, truth, scale_as=None):
        """
        Parameters
        ----------
        prediction : array of shape (N,)
            values predicted by the machine learning regressor
        
        truth : array of shape (N,)
            the true values to test `prediction` against
        
        scale_as : callable (default = None)
            function of `truth` over which the error scales (i.e., ``residual = (prediction-truth)/scale_as(truth)``). By default, assume error is uniform over `truth` (i.e., ``scale_as = lambda x: 1``). CAUTION: A function which can output zero for a possible value of `truth` may raise a RuntimeWarning and produce infinities
        """
        self.scale_as = scale_as
        self.prediction = np.asarray(prediction)
        self.truth = np.asarray(truth)
        if truth.shape != prediction.shape:
            raise ValueError("`truth` and `prediction` must have same length")
        self.res = (self.prediction - self.truth) 
        if not scale_as is None:
            self.res /= self.scale_as(self.truth.copy())
    
    def nmad(self):
        """
        Return the Normalized Median Absolute Deviation of the residuals
        
        :math:`\\sigma_{\\rm NMAD}` = 1.48 * ``median(abs(residual))``
        """
        return 1.48 * np.median(np.abs(self.res))
    
    def std(self):
        """
        Return the standard deviation, :math:`\\sigma`, of the residuals
        """
        return np.std(self.res, ddof=1)
    
    def r2(self):
        """
        Return the R^2 score of the prediction vs. truth
        """
        return sklearn.metrics.r2_score(self.truth, self.prediction)
    
    def outlier_frac(self, outlier_sigmas=3, spread_estimator="nmad"):
        """
        Return the outlier fraction of predictions. By default, an outlier is defined by having a residual of magnitude greater than :math:`3\\sigma_{\\rm NMAD}`.
        
        Parameters
        ----------
        outlier_sigmas : float, int (default = 3)
            The number of sigmas to count a residual as an outlier
        
        spread_estimator : string (default = "nmad")
            Either "nmad" or "std" to specify the function to estimate the spread of the distribution of residuals
        """
        n_out =  np.sum( self.is_outlier(outlier_sigmas, spread_estimator) )
        return n_out / float(len(self.res))
    
    def is_outlier(self, outlier_sigmas=3, spread_estimator="nmad"):
        """
        Return a boolean mask which is True for the index of each outlier
        
        Parameters
        ----------
        See parameters of `outlier_frac()`
        """
        spread_estimator = self._choose_spread_estimator(spread_estimator)
        spread = spread_estimator()
        return np.abs(self.res) > (outlier_sigmas*spread)
    
    def plot_residuals(self, target_label="x", f_label=None, 
                       outlier_sigmas=3, spread_estimator="nmad", 
                       color=["b","r"], ax=None, fontsize=14, 
                       res=True, **scatter_kwargs):
        """
        Make a plot of the residuals, distinguishing clearly between residuals which are outliers and those which are not. By default, an outlier is defined by having a residual of magnitude greater than :math:`3\\sigma_{\\rm NMAD}`.
        
        Parameters
        ----------
        target_label : string (default = "x")
            The string to use in the label identifying the quantity you are trying to predict
        
        f_label : callable (default = None)
            Takes single argument (target_label string) and returns the string to use to identify the function over which the error scales
        
        outlier_sigmas : float, int (default = 3)
            The number of sigmas to count a residual as an outlier
        
        spread_estimator : string (default = "nmad")
            Either "nmad" or "std" to specify the function to estimate the spread of the distribution of residuals
        
        color : list of strings of length 2 (default = ["b","r"])
            Zeroth element specifies the color of non-outliers, and first element specifies the color of outliers
        
        ax : matplotlib.Axes object (default = plt.gca())
            Axis on which to draw this plot. By default, use the most recently updated axis or create a new one if none are available.
        
        fontsize : float, int (default = 14)
            Font size for labels and title
        
        res : boolean (default = True)
            If True, plot scaled residual vs. truth. If False, plot prediction vs. truth
        
        **scatter_kwargs : various types (default = {s=1, alpha=0.1})
            Additional keyword arguments will be stored and given to plt.scatter()
        """
        spread_label = self._choose_spread_label(spread_estimator)
        spread_estimator = self._choose_spread_estimator(spread_estimator)
        
        if ax is None: ax = plt.gca()
        
        spread = spread_estimator()
        is_outlier = np.abs(self.res) > (outlier_sigmas*spread)
        outlier_frac = np.sum(is_outlier) / float(len(self.truth))
        
        scatter_kwargs["s"] = scatter_kwargs.get("s", 1)
        scatter_kwargs["alpha"] = scatter_kwargs.get("alpha", .1)
        
        y = self.res if res else self.prediction
        ax.scatter(self.truth[~is_outlier], y[~is_outlier], 
                    color=color[0], **scatter_kwargs)
        ax.scatter(self.truth[is_outlier], y[is_outlier],
                    color=color[1], **scatter_kwargs)
        
        if res:
            ax.axhline(outlier_sigmas * spread, color="k", ls="--")
            ax.axhline(- outlier_sigmas * spread, color="k", ls="--")
        else:
            x = np.linspace(self.truth.min(), self.truth.max(), 1000)
            scaling = 1 if self.scale_as is None else self.scale_as(x.copy())
            upperlim = x + outlier_sigmas * spread * scaling
            lowerlim = x - outlier_sigmas * spread * scaling
            ax.plot(x,upperlim,"k--")
            ax.plot(x,lowerlim,"k--")
            ax.set_ylim(ax.get_xlim(), auto=True)
            
        
        
        t = f"{target_label}_{{\\rm truth}}"
        p = f"{target_label}_{{\\rm predicted}}"
        ax.set_xlabel(f"${t}$", fontsize=fontsize)
        ax.set_title(f"${spread_label}=${spread:.3e}\n$3\\sigma$ outliers$=${outlier_frac*100:.3f}%\n$R^2=${self.r2():.4f}", fontsize=fontsize)
        if not res:
            ax.set_ylabel(f"${p}$", fontsize=fontsize)
        else:
            if not f_label is None:
                ax.set_ylabel(f"$\\frac{{({p}-{t})}}{{{f_label(t)}}}$", fontsize=1.3*fontsize)
            elif self.scale_as is None:
                ax.set_ylabel(f"${p}-{t}$", fontsize=fontsize)
            else:
                ax.set_ylabel(f"$\\frac{{({p}-{t})}}{{f({t})}}$", fontsize=1.3*fontsize)
    

    def _choose_spread_estimator(self, spread_estimator):
        """
        Parse the input string to choose which spread estimator we are using
        Options: {'nmad', 'std'}
        """
        if spread_estimator.lower() == "nmad":
            spread_estimator = self.nmad
        elif spread_estimator.lower() == "std":
            spread_estimator = self.std
        else:
            raise ValueError("Invalid option for `spread_estimator`. Must be in {'nmad', 'std'}")
        return spread_estimator
    
    def _choose_spread_label(self, spread_estimator):
        """
        Parse the input string to choose the label for the plot
        Options: {'nmad', 'std'}
        """
        if spread_estimator.lower() == "nmad":
            return "\\sigma_{\\rm NMAD}"
        elif spread_estimator.lower() == "std":
            return "\\sigma"
        else:
            raise ValueError("Invalid option for `spread_estimator`. Must be in {'nmad', 'std'}")