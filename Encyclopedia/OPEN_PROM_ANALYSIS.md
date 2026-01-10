# OPEN-PROM GAMS to Python Conversion Analysis

## Repository: https://github.com/e3modelling/OPEN-PROM

---

## 1. GAMS Code Structure Review

### 1.1 Overall Architecture

OPEN-PROM is a **modular energy system optimization model** with a well-organized structure:

```
OPEN-PROM/
├── main.gms                    # Main entry point
├── core/                       # Core model components
│   ├── sets.gms               # Set definitions
│   ├── declarations.gms       # Variable/parameter declarations
│   ├── input.gms              # Input data loading
│   ├── equations.gms          # Core equations
│   ├── preloop.gms            # Pre-solve calculations
│   ├── solve.gms              # Solver configuration & execution
│   └── postsolve.gms          # Post-solve processing
├── modules/                    # Sector-specific modules
│   ├── 01_Transport/
│   ├── 02_Industry/
│   ├── 03_RestOfEnergy/
│   ├── 04_PowerGeneration/
│   ├── 05_Hydrogen/
│   ├── 06_CO2/
│   ├── 07_Emissions/
│   ├── 08_Prices/
│   └── 09_Heat/
├── scripts/                    # Data processing scripts
└── tutorials/                  # Documentation & examples
```

### 1.2 Naming Convention

The model uses a **strict naming convention** that must be preserved:

- **Variables:**
  - `Vm*` = Model-wide/interdependent variables (shared across modules)
  - `Vxx*` = Module-specific variables (xx = module number, e.g., V01, V02)
  - `V*` = Core-only variables

- **Equations:**
  - `Qxx*` = Must start with 2-digit module code (e.g., Q01, Q02)

- **Inputs/Parameters:**
  - `im*` = Model-wide inputs
  - `ixx*` = Module-specific inputs

**Example:**
- `VmLft(allCy,DSBS,EF,YTIME)` - Lifetime of technologies (shared)
- `V01ActivGoodsTransp(allCy,TRANSE,YTIME)` - Transport activity (module 01)
- `Q01RateScrPc(allCy,YTIME)` - Scrapping rate equation (module 01)

### 1.3 Model Execution Flow

From `main.gms`, the execution follows this sequence:

1. **Preliminaries** - Configuration flags, dollar commands
2. **Data Loading** - R scripts (`loadMadratData.R`) for input data
3. **Sets** - Define indices (countries, technologies, time periods, etc.)
4. **Declarations** - Declare variables and parameters
5. **Inputs** - Load parameter values
6. **Equations** - Define constraints and objective
7. **Preloop** - Pre-solve calculations
8. **Solve** - Execute optimization
9. **Postsolve** - Post-processing and output generation

### 1.4 Module Structure

Each module follows a consistent pattern:
- Sets definitions
- Variable/parameter declarations
- Input data
- Equations
- Preloop calculations
- Postsolve processing

### 1.5 Key Features

- **Time Horizon:** 2010-2100 (configurable)
- **Geographic Scope:** Multi-country (configurable country sets)
- **Solver Configuration:** Uses CONOPT (nonlinear) and other solvers
- **Data Integration:** R scripts for data preparation
- **Output:** GDX files, R scripts for reporting

---

## 2. Optimization Problem Type Identification

### 2.1 Problem Classification

Based on the model structure and PROMETHEUS documentation, OPEN-PROM is a:

**Mixed-Integer Nonlinear Programming (MINLP) / Nonlinear Programming (NLP) Model**

**Evidence:**
- Uses CONOPT solver (designed for NLP)
- Energy system models typically involve:
  - **Linear relationships:** Energy balances, capacity constraints
  - **Nonlinear relationships:** Learning curves, efficiency curves, cost functions
  - **Integer decisions:** Investment decisions, technology choices (binary/integer variables)

### 2.2 Typical Problem Components

1. **Objective Function:**
   - Likely minimizes total system cost (investment + operating costs)
   - May include carbon pricing/emissions penalties

2. **Constraints:**
   - **Energy balances:** Supply = Demand for each energy carrier
   - **Capacity constraints:** Generation ≤ Capacity
   - **Investment constraints:** Technology deployment limits
   - **Resource constraints:** Renewable potential, fuel availability
   - **Policy constraints:** Emissions targets, renewable shares
   - **Temporal constraints:** Technology lifetimes, ramp rates

3. **Decision Variables:**
   - Investment in technologies (continuous or integer)
   - Energy production/consumption (continuous)
   - Capacity utilization (continuous)
   - Technology choices (binary/integer)

### 2.3 Problem Scale

- **Dimensions:** Multi-country, multi-technology, multi-time period
- **Complexity:** Large-scale (thousands to tens of thousands of variables/constraints)
- **Solver Requirements:** Robust NLP/MINLP solver needed

---

## 3. Recommended Python Framework

### 3.1 Primary Recommendation: **Pyomo**

**Why Pyomo:**
1. **GAMS-like syntax** - Easiest transition from GAMS
2. **Comprehensive solver support** - Works with CPLEX, Gurobi, IPOPT, CONOPT, CBC, etc.
3. **Flexible modeling** - Supports LP, NLP, MIP, MINLP
4. **Active development** - Well-maintained, large community
5. **Modular design** - Can structure code similar to GAMS modules
6. **Data integration** - Works well with Pandas, NumPy

**Pyomo Structure Example:**
```python
from pyomo.environ import *

model = ConcreteModel()

# Sets
model.countries = Set()
model.technologies = Set()
model.time_periods = Set()

# Parameters
model.cost = Param(model.technologies, model.time_periods)

# Variables
model.investment = Var(model.technologies, model.time_periods, domain=NonNegativeReals)

# Constraints
def energy_balance_rule(model, country, time):
    return sum(model.production[tech, country, time] for tech in model.technologies) == \
           model.demand[country, time]
model.energy_balance = Constraint(model.countries, model.time_periods, rule=energy_balance_rule)

# Objective
def total_cost_rule(model):
    return sum(model.cost[tech, t] * model.investment[tech, t] 
               for tech in model.technologies for t in model.time_periods)
model.total_cost = Objective(rule=total_cost_rule, sense=minimize)
```

### 3.2 Alternative Options

#### Option 2: **GAMSPy** (New, GAMS-backed)
- **Pros:** Uses GAMS backend, high performance, familiar to GAMS users
- **Cons:** Requires GAMS license, newer/less mature
- **Best for:** If you want to keep GAMS solver but use Python interface

#### Option 3: **CVXPY** (Convex optimization)
- **Pros:** Clean syntax, good for convex problems
- **Cons:** Limited to convex problems, may not handle all MINLP aspects
- **Best for:** If the model can be reformulated as convex

#### Option 4: **OR-Tools** (Google)
- **Pros:** Excellent for MIP, good performance
- **Cons:** Less suitable for pure NLP, different modeling style
- **Best for:** If model is primarily MIP

### 3.3 Solver Recommendations

For Pyomo:
- **NLP:** IPOPT (open-source), CONOPT (commercial, if available)
- **MIP:** CBC (open-source), CPLEX/Gurobi (commercial)
- **MINLP:** BONMIN (open-source), DICOPT (commercial)

---

## 4. Conversion Strategy

### 4.1 Phase 1: Analysis & Planning (Week 1-2)

**Tasks:**
1. **Deep dive into GAMS code:**
   - Map all sets, parameters, variables, equations
   - Document data flow between modules
   - Identify interdependencies
   - Understand solver settings and options

2. **Create mapping document:**
   - GAMS sets → Python sets/lists
   - GAMS parameters → Pandas DataFrames/dictionaries
   - GAMS variables → Pyomo Variables
   - GAMS equations → Pyomo Constraints
   - GAMS model → Pyomo ConcreteModel

3. **Data pipeline analysis:**
   - Understand R script data loading
   - Plan Python equivalent (Pandas, data processing)
   - Identify input data formats (CSV, GDX, etc.)

### 4.2 Phase 2: Core Infrastructure (Week 3-4)

**Tasks:**
1. **Set up Python project structure:**
   ```
   open_prom_py/
   ├── core/
   │   ├── sets.py
   │   ├── declarations.py
   │   ├── inputs.py
   │   ├── equations.py
   │   ├── solve.py
   │   └── postsolve.py
   ├── modules/
   │   ├── transport/
   │   ├── industry/
   │   ├── power_generation/
   │   └── ...
   ├── data/
   ├── scripts/
   └── tests/
   ```

2. **Implement core components:**
   - Set definitions (Python sets/dictionaries)
   - Configuration system (YAML/JSON for flags)
   - Data loading utilities
   - Logging and error handling

3. **Create base model class:**
   ```python
   class OpenPromModel:
       def __init__(self, config):
           self.model = ConcreteModel()
           self.config = config
           self.load_sets()
           self.load_parameters()
           self.create_variables()
           self.create_equations()
           self.create_objective()
   ```

### 4.3 Phase 3: Module-by-Module Conversion (Week 5-12)

**Strategy:**
- Convert one module at a time
- Start with simplest module (e.g., Prices, CO2)
- Progress to more complex modules (Transport, Power Generation)
- Test each module independently before integration

**For each module:**
1. Translate sets
2. Translate parameters (load from data files)
3. Translate variables
4. Translate equations
5. Create unit tests
6. Validate against GAMS output

**Module Priority:**
1. **Core** (sets, basic equations)
2. **08_Prices** (likely simpler, foundational)
3. **06_CO2** (emissions accounting)
4. **07_Emissions** (emissions calculations)
5. **04_PowerGeneration** (complex but critical)
6. **01_Transport** (complex, many technologies)
7. **02_Industry** (complex)
8. **03_RestOfEnergy** (legacy module)
9. **05_Hydrogen** (emerging technology)
10. **09_Heat** (sector-specific)

### 4.4 Phase 4: Integration & Testing (Week 13-16)

**Tasks:**
1. **Integrate all modules:**
   - Connect module interfaces
   - Handle shared variables (Vm*)
   - Ensure data flow consistency

2. **Solver integration:**
   - Configure solver options
   - Test with different solvers
   - Optimize solver settings

3. **Validation:**
   - Run same scenarios as GAMS version
   - Compare results (objective value, key variables)
   - Identify and fix discrepancies
   - Performance benchmarking

4. **Data pipeline:**
   - Replace R scripts with Python equivalents
   - Implement data loading from various sources
   - Create output generation (replace R reporting)

### 4.5 Phase 5: Optimization & Documentation (Week 17-20)

**Tasks:**
1. **Performance optimization:**
   - Profile code
   - Optimize data structures
   - Parallel processing where possible
   - Memory optimization

2. **Documentation:**
   - API documentation
   - User guide
   - Migration guide from GAMS
   - Tutorials

3. **Testing:**
   - Comprehensive test suite
   - Regression tests
   - Integration tests

### 4.6 Key Conversion Challenges & Solutions

#### Challenge 1: GAMS Dollar Commands
**Solution:** Use Python configuration files (YAML/JSON) and conditional logic

#### Challenge 2: GDX File I/O
**Solution:** Use `gdxpds` or `gams2pyomo` utilities, or convert to CSV/Parquet

#### Challenge 3: R Script Integration
**Solution:** Rewrite in Python using Pandas, or use `rpy2` as interim solution

#### Challenge 4: Complex Indexing
**Solution:** Use Pandas MultiIndex or structured NumPy arrays

#### Challenge 5: Equation Complexity
**Solution:** Break into helper functions, use Pyomo's expression builders

#### Challenge 6: Solver Compatibility
**Solution:** Test multiple solvers, provide solver abstraction layer

---

## 5. Recommended Tools & Libraries

### 5.1 Core Dependencies

```python
# Optimization
pyomo>=6.5.0
pyomo.extras>=1.0.0  # Additional utilities

# Data handling
pandas>=2.0.0
numpy>=1.24.0
pyarrow>=12.0.0  # For Parquet files
openpyxl>=3.1.0  # For Excel files

# GDX file support (if needed)
gdxpds>=1.3.0  # Read/write GDX files

# Configuration
pyyaml>=6.0
pydantic>=2.0  # For config validation

# Utilities
tqdm>=4.65.0  # Progress bars
loguru>=0.7.0  # Logging
```

### 5.2 Solver Options

```python
# Open-source
ipopt  # NLP solver
cbc  # MIP solver
bonmin  # MINLP solver

# Commercial (if licenses available)
# cplex, gurobi, conopt
```

### 5.3 Development Tools

```python
# Testing
pytest>=7.4.0
pytest-cov>=4.1.0

# Code quality
ruff>=0.1.0  # Linter
black>=23.0.0  # Formatter
mypy>=1.5.0  # Type checking

# Documentation
sphinx>=7.0.0
```

---

## 6. Project Structure Template

```
open_prom_py/
├── README.md
├── pyproject.toml
├── requirements.txt
├── config/
│   ├── default.yaml
│   └── scenarios/
├── open_prom/
│   ├── __init__.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── model.py          # Main model class
│   │   ├── sets.py
│   │   ├── declarations.py
│   │   ├── inputs.py
│   │   ├── equations.py
│   │   ├── solve.py
│   │   └── postsolve.py
│   ├── modules/
│   │   ├── __init__.py
│   │   ├── transport/
│   │   ├── industry/
│   │   ├── power_generation/
│   │   └── ...
│   ├── data/
│   │   ├── loaders/
│   │   └── processors/
│   ├── utils/
│   │   ├── config.py
│   │   ├── logging.py
│   │   └── gdx_io.py
│   └── solvers/
│       └── solver_manager.py
├── scripts/
│   ├── load_data.py
│   ├── run_model.py
│   └── compare_results.py
├── tests/
│   ├── test_core/
│   ├── test_modules/
│   └── fixtures/
└── docs/
    ├── user_guide.md
    ├── api_reference.md
    └── migration_guide.md
```

---

## 7. Next Steps

1. **Clone and explore the repository in detail**
2. **Identify a simple module to start with** (e.g., Prices or CO2)
3. **Set up Python project structure**
4. **Create a proof-of-concept** for one module
5. **Establish testing framework** to validate against GAMS
6. **Plan data pipeline** replacement for R scripts

---

## 8. Resources

- **Pyomo Documentation:** https://pyomo.readthedocs.io/
- **GAMS to Pyomo Guide:** https://pyomo.readthedocs.io/en/stable/working_models/index.html
- **PROMETHEUS Documentation:** https://e3modelling.com/modelling-tools/prometheus/
- **GAMSPy:** https://www.gams.com/blog/2024/12/gamspy-high-performance-optimization-in-python/

---

**Estimated Timeline:** 4-5 months for full conversion with testing and validation

**Recommended Approach:** Start with a proof-of-concept for one module to validate the approach before full conversion.







