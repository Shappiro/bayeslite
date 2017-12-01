[Experimental] Bayeslite Analysis Reference
===========================================

If you would like to analyze your own data with BayesDB, please
contact bayesdb@mit.edu to participate in our research project.

BQL Data Modelling Commands
---------------------------

.. index:: ``CREATE GENERATOR``

``CREATE GENERATOR <name> [IF NOT EXISTS] FOR <table> USING <backend> (<schema>)``

   Create a generative model named *name* for the table named *table*
   in the language of *backend*.  *Schema* describes the generative
   model in syntax that depends on the backend.  Typically, it is a
   comma-separated list of clauses of the form

      ``<column> <type>``

   requesting the column *column* to be modelled with the statistical
   type *type*, with some additional types of clauses.  For example,

   .. code-block:: sql

      CREATE GENERATOR t_cc FOR t USING crosscat (
          SUBSAMPLE(1000),      -- Subsample down to 1000 rows;
          GUESS(*),             -- guess all column types, except
          name IGNORE,          -- ignore the name column, and
          angle CYCLIC          -- treat angle as CYCLIC.
      )

.. index:: ``DROP GENERATOR``

``DROP GENERATOR [IF EXISTS] <name>``

   Drop the generator named *name* and all its models.

.. index:: ``ALTER GENERATOR``

``ALTER GENERATOR <name> <alterations>``

   Alter the specified properties of the generator named *name*.
   *Alterations* is a comma-separated list of alterations.  The
   following alterations are supported:

   .. index:: ``RENAME TO``

   ``RENAME TO <newname>``

      Change the generator's name to *newname*.

.. index:: ``INITIALIZE MODELS``

``INITIALIZE <n> MODEL[S] [IF NOT EXISTS] FOR <name>``

   Perform backend-specific initialization of up to *n* models for
   the generator named *name*.  *n* must be a literal integer.  If the
   generator already had models, the ones it had are unchanged.
   Models are zero-indexed.

.. index:: ``DROP MODELS``

``DROP MODELS [<modelset>] FROM <name>``

   Drop the specified models from the generator named *name*.
   *Modelset* is a comma-separated list of model numbers or hyphenated
   model number ranges, inclusive on both bounds.  If *modelset* is
   omitted, all models are dropped from the generator.

   Example:

      ``DROP MODELS 1-3 FROM t_cc``

   Equivalent:

      ``DROP MODEL 1 FROM t_cc; DROP MODEL 2 FROM t_cc; DROP MODEL 3 FROM t_cc``

.. index:: ``ANALYZE MODELS``

``ANALYZE <name> [MODEL[S] <modelset>] [FOR <duration>] [CHECKPOINT <duration>] WAIT``

   Perform backend-specific analysis of the specified models of the
   generator *name*.  *Modelset* is a comma-separated list of model
   numbers or hyphenated model number ranges.  *Duration* is either
   ``<n> SECOND[S]``, ``<n> MINUTE[S]``, or ``<n> ITERATION[S]``.

   The ``FOR`` duration specifies how long to perform analysis.  The
   ``CHECKPOINT`` duration specifies how often to commit the
   intermediate results of analysis to the database on disk.

   Examples:

      ``ANALYZE t_cc FOR 10 MINUTES CHECKPOINT 30 SECONDS``

      ``ANALYZE t_cc MODELS 1-3,7-9 FOR 10 ITERATIONS CHECKPOINT 1 ITERATION``


:mod:`bayeslite.backend`: Bayeslite backend interface
---------------------------------------------------------

.. automodule:: bayeslite.backend
   :members:

:mod:`bayeslite.guess`: Heuristics for statistical types
--------------------------------------------------------

.. automodule:: bayeslite.guess
    :members:
