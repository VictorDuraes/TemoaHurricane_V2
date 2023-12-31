from pyomo.environ import *
from math import isclose
import math
import copy

# ---------------------------------------------
# @ex1
from pyomo.core.expr import current as EXPR

M = ConcreteModel()
M.x = Var()

e = sin(M.x) + 2 * M.x

# sin(x) + 2*x
print(EXPR.expression_to_string(e))

# sum(sin(x), prod(2, x))
print(EXPR.expression_to_string(e, verbose=True))
# @ex1

# ---------------------------------------------
# @ex2
from pyomo.core.expr import current as EXPR

M = ConcreteModel()
M.x = Var()
M.y = Var()

e = sin(M.x) + 2 * M.y

# sin(x1) + 2*x2
print(EXPR.expression_to_string(e, labeler=NumericLabeler('x')))
# @ex2

# ---------------------------------------------
# @ex3
from pyomo.core.expr import current as EXPR

M = ConcreteModel()
M.x = Var()
M.y = Var()

e = sin(M.x) + 2 * M.y + M.x * M.y - 3

# -3 + 2*y + sin(x) + x*y
print(EXPR.expression_to_string(e, standardize=True))
# @ex3

# ---------------------------------------------
# @ex4
from pyomo.core.expr import current as EXPR

M = ConcreteModel()
M.x = Var()

with EXPR.clone_counter() as counter:
    start = counter.count
    e1 = sin(M.x)
    e2 = e1.clone()
    total = counter.count - start
    assert total == 1
# @ex4

# ---------------------------------------------
# @ex5
M = ConcreteModel()
M.x = Var()
M.x.value = math.pi / 2.0
val = value(M.x)
assert isclose(val, math.pi / 2.0)
# @ex5
# @ex6
val = M.x()
assert isclose(val, math.pi / 2.0)
# @ex6

# ---------------------------------------------
# @ex7
M = ConcreteModel()
M.x = Var()
val = value(M.x, exception=False)
assert val is None
# @ex7

# ---------------------------------------------
# @ex8
from pyomo.core.expr import current as EXPR

M = ConcreteModel()
M.x = Var()
M.p = Param(mutable=True)

e = M.p + M.x
s = set([type(M.p)])
assert list(EXPR.identify_components(e, s)) == [M.p]
# @ex8

# ---------------------------------------------
# @ex9
from pyomo.core.expr import current as EXPR

M = ConcreteModel()
M.x = Var()
M.y = Var()

e = M.x + M.y
M.y.value = 1
M.y.fixed = True

assert set(id(v) for v in EXPR.identify_variables(e)) == set([id(M.x), id(M.y)])
assert set(id(v) for v in EXPR.identify_variables(e, include_fixed=False)) == set(
    [id(M.x)]
)
# @ex9

# ---------------------------------------------
# @visitor1
from pyomo.core.expr import current as EXPR


class SizeofVisitor(EXPR.SimpleExpressionVisitor):
    def __init__(self):
        self.counter = 0

    def visit(self, node):
        self.counter += 1

    def finalize(self):
        return self.counter


# @visitor1


# ---------------------------------------------
# @visitor2
def sizeof_expression(expr):
    #
    # Create the visitor object
    #
    visitor = SizeofVisitor()
    #
    # Compute the value using the :func:`xbfs` search method.
    #
    return visitor.xbfs(expr)


# @visitor2

# ---------------------------------------------
# @visitor3
from pyomo.core.expr import current as EXPR


class CloneVisitor(EXPR.ExpressionValueVisitor):
    def __init__(self):
        self.memo = {'__block_scope__': {id(None): False}}

    def visit(self, node, values):
        #
        # Clone the interior node
        #
        return node.construct_clone(tuple(values), self.memo)

    def visiting_potential_leaf(self, node):
        #
        # Clone leaf nodes in the expression tree
        #
        if (
            node.__class__ in native_numeric_types
            or node.__class__ not in pyomo5_expression_types
        ):
            return True, copy.deepcopy(node, self.memo)

        return False, None


# @visitor3


# ---------------------------------------------
# @visitor4
def clone_expression(expr):
    #
    # Create the visitor object
    #
    visitor = CloneVisitor()
    #
    # Clone the expression using the :func:`dfs_postorder_stack`
    # search method.
    #
    return visitor.dfs_postorder_stack(expr)


# @visitor4

# ---------------------------------------------
# @visitor5
from pyomo.core.expr import current as EXPR


class ScalingVisitor(EXPR.ExpressionReplacementVisitor):
    def __init__(self, scale):
        super(ScalingVisitor, self).__init__()
        self.scale = scale

    def visiting_potential_leaf(self, node):
        #
        # Clone leaf nodes in the expression tree
        #
        if node.__class__ in native_numeric_types:
            return True, node

        if node.is_variable_type():
            return True, self.scale[id(node)] * node

        if isinstance(node, EXPR.LinearExpression):
            node_ = copy.deepcopy(node)
            node_.constant = node.constant
            node_.linear_vars = copy.copy(node.linear_vars)
            node_.linear_coefs = []
            for i, v in enumerate(node.linear_vars):
                node_.linear_coefs.append(node.linear_coefs[i] * self.scale[id(v)])
            return True, node_

        return False, None


# @visitor5


# ---------------------------------------------
# @visitor6
def scale_expression(expr, scale):
    #
    # Create the visitor object
    #
    visitor = ScalingVisitor(scale)
    #
    # Scale the expression using the :func:`dfs_postorder_stack`
    # search method.
    #
    return visitor.dfs_postorder_stack(expr)


# @visitor6

# ---------------------------------------------
# @visitor7
M = ConcreteModel()
M.x = Var(range(5))
M.p = Param(range(5), mutable=True)

scale = {}
for i in M.x:
    scale[id(M.x[i])] = M.p[i]

e = quicksum(M.x[i] for i in M.x)
f = scale_expression(e, scale)

# p[0]*x[0] + p[1]*x[1] + p[2]*x[2] + p[3]*x[3] + p[4]*x[4]
print(f)
# @visitor7
