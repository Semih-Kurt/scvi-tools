===========
CellAssign
===========

**CellAssign** [#ref1]_ (Python class :class:`~scvi.external.CellAssign`) is a simple yet, efficient
approach for annotating scRNA-seq data in the scenario in which cell-type-specific
gene markers are known. The method also allows users to control for nuisance covariates
like batch or donor. The scvi-tools implementation of CellAssign uses stochastic inference,
such that CellAssign will scale to very large datasets.

The advantages of CellAssign are:

- Lightweight model that can be fit quickly.
- Ability to control for nuisance factors.

The limitations of CellAssign include:

- Requirement for a cell types by gene markers binary matrix.
- The simple linear model may not handle non-linear batch effects.


.. topic:: Tutorials:

 - :doc:`/tutorials/notebooks/cellassign_tutorial`


Preliminaries
==============
CellAssign takes as input a scRNA-seq gene expression matrix :math:`X` with :math:`N` cells and :math:`G` genes
along with a cell-type marker matrix :math:`\rho` which is a binary matrix of :math:`G` genes by :math:`C` cell types
denoting if a gene is a marker of a particular cell type. A size factor :math:`s` for each cell may also
be provided as input, otherwise it is computed empirically as the total unique molecular identifier
count of a cell. Additionally, a design matrix :math:`D` containing :math:`p` observed covariates,
such as day, donor, etc, is an optional input.


Generative process
========================

CellAssign uses a negative binomial mixture model to make cell-type predictions.
The cell-type proportion is drawn from a Dirichlet distribution,

.. math::

    (\pi_1, ..., \pi_C) \sim \textrm{Dirichlet}(\alpha, ..., \alpha), \tag{1}

with :math:`\alpha = 0.01`.

CellAssign then posits that the observed gene expression counts :math:`x_{ng}` for cell :math:`n`
and gene :math:`g` are generated by the following process:

.. math::
   :nowrap:

   \begin{align}
      \delta_{gc} &\sim \textrm{LogNormal}(\bar{\delta}, \sigma^2)   \tag{2} \\
      \log \mu _{ngc} &= \log s_n + \delta _{gc}\rho _{gc}+ \beta _{g0}+ \sum_p{\beta _{gp}d_{pn}} \label{a} \tag{3}\\
      \tilde \phi _{ngc} &= \sum_{i = 1}^B {a_i \times \exp ({ - b \times ( {\mu _{ngc} - v_i})^2})} \label{b} \tag{4}\\
      z_n &\sim \textrm{Discrete}(\pi) \tag{5}\\
      x_{ng} \mid z_n = c &\sim \textrm{NegativeBinomial}(\mu_{ngc}, \tilde \phi _{ngc}) \tag{6}
   \end{align}

Notably, the logarithm of the mean of the negative binomial for cell $n$, gene :math:`g`, given that it belongs
to cell type :math:`c` (Equation :math:`\ref{a}`) is computed as the sum of (1) the base expression of a gene :math:`g`, :math:`\beta_{g0}`, (2) a
cell-type-specific overexpression term for a gene, :math:`\delta_{gc}`, (3) an offset for the size
factor, :math:`\log s_n`, and (4) a linear combination of covariates in the design
matrix (weighted by coefficients :math:`\beta_{gi}`). A cell-specific discrete latent variable, :math:`z_n`,
represents the cell-type assignment for cell $n$.

Furthermore, the inverse dispersion of the negative binomial, :math:`\tilde{\phi}_{ngc}` (Equation :math:`\ref{b}`) is computed with a sum of radial basis functions of the mean centered on $v_i$ with parameters $a_i$ and $b$. In total, there are $B$ centers $v_1, v_2, ..., v_{10}$ that are set a priori to be equally spaced between 0 and the maximum count value of $X$.
Additionally, as in the original implementation we used :math:`B=10`. The parameters :math:`a_i` and :math:`b` are
further described below.

Inference
========================
CellAssign uses expectation maximization (EM) to optimize its parameters and provides a cell-type prediction for each cell.

Initialization
--------------

CellAssign initializes parameters as follows:  :math:`\delta_{gc}` is initialized with a :math:`\textrm{LogNormal}(0, 1)`
draw, :math:`\bar{\delta}` is initialized to 0, :math:`\sigma^2` is initialized to 1, :math:`\pi_i` is
initialized to :math:`1/C`, :math:`\beta_{gi}` is initialized with a :math:`\mathcal{N}(0, 1)` draw,
and the inverse dispersion parameter :math:`\log a_i` is initialized to 0. Additionally, :math:`b` is fixed a priori to be

.. math::
    b = \frac{1}{2(v_2 - v_1)^2}, \tag{7}

where :math:`v_1` and :math:`v_2` are the first and second center determined as stated previously.

E step
-------

The E step consists of computing the expected joint log likelihood with respect to the conditional posterior,
:math:`p(z_n \mid x_n, \delta, \beta, a, \pi)`, for each cell. This conditional posterior is
computed in closed form as

.. math::

    \gamma_{nc} := p(z_n = c \mid x_n, \delta, \beta, a, \pi) \propto p(z_n = c \mid \pi)\prod_g p(x_{ng} \mid \mu_{ngc}, \tilde{\phi}_{ngc}), \tag{8}

which is normalized over all $c$. The expected joint log likelihood over all :math:`N` cells is then computed as

.. math::
   :nowrap:

    \begin{align}
        \begin{split}
        \mathbb{E}_{z \mid X,\pi,\delta, \beta, a}[\log p(X, \pi, \delta \mid \beta, a, \bar{\delta}, \sigma^2)]
        % &=\log p(\theta) + \log p(\delta) +\sum_n\sum_{c}\gamma_{nc}\log p(y_{n}|c)\\
        &= \sum_{n=1}^{N}\sum_{c=1}^{C}\gamma_{nc}\sum_{g=1}^{G}\log p(x_{ng}|z_n = c) \\
        & \qquad + \log p(\pi) + \log p(\delta).
        \end{split} \tag{9}
    \end{align}

Herein lies the major difference between the scvi-tools implementation and the original CellAssign implementation.
Notably, in scvi-tools we compute this expected joint log likelihood using a mini-batch of 1,024 cells, using the fact that

.. math::

    \sum_{n=1}^{N}\sum_{c=1}^{C}\gamma_{nc}\sum_{g=1}^{G}\log p(x_{ng}|z_n = c) \approx \frac{N}{M}\sum_{m=1}^M\sum_{c=1}^{C}\gamma_{nc}\sum_{g=1}^{G}\log p(x_{\tau(m)g}|z_n = c) \tag{10}

for a minibatch of $M<N$ cells, where :math:`\tau` is a function describing a permutation of the data indices $\{1, 2, ..., N\}$.

M step
-------

The parameters of the expected joint log likelihood (:math:`\pi, \delta, \beta, a, \bar{\delta}, \sigma^2`) are optimized as
in the original implementation [#ref2]_, using the Adam optimizer [#ref3]_, except that now an optimization step corresponds to data from one minibatch. Following the original implementation, we
also clamped :math:`\delta > 2`. We also added early stopping with respect to the log likelihood of a held-out validation set.

Tasks
=====

Cell type prediction
---------------------

The primary task of CellAssign is to predict cell types for each cell. This is accomplished by::

    >>> model = CellAssign(adata, marker_gene_matrix, size_factor_key='size_factor')
    >>> model.train()
    >>> predictions = model.predict(adata)

where `predictions` stores :math:`\gamma_{nc}` for each cell :math:`n` and cell type :math:`c`.


Implementation details
======================

The logic implementing CellAssign can be found in :class:`scvi.external.cellassign.CellAssignModule`.
The implementation uses the same variable names as the math.

    + The core logic is implemented in :func:`scvi.external.cellassign.CellAssignModule.generative`. In this method, the E step is taken
      and the log likelihood :math:`\log p(X \mid \beta, a, \bar{\delta}, \sigma^2, z_n=c)` is computed for all cell types.

    + In :func:`scvi.external.cellassign.CellAssignModule.loss` the full expected log likelihood is computed, as well as
      the penalities corresponding to the priors on :math:`\pi` and :math:`\delta`.

    + CellAssign uses the standard :class:`~scvi.train.TrainingPlan`.

.. topic:: References:

   .. [#ref1] Allen W. Zhang, Ciara O’Flanagan, Elizabeth A. Chavez, Jamie LP Lim, Nicholas Ceglia, Andrew McPherson, Matt Wiens et al. (2019),
        *Probabilistic cell-type assignment of single-cell RNA-seq for tumor microenvironment profiling*,
        `Nature Methods <https://www.nature.com/articles/s41592-019-0529-1?elqTrackId=12c8cef68e0741ef8422778b61>`__.
   .. [#ref2] CellAssign original implementation. GitHub. https://github.com/Irrationone/cellassign
   .. [#ref3] Kingma, Diederik P., and Jimmy Ba. "Adam: A method for stochastic optimization." arXiv preprint arXiv:1412.6980 (2014).
