
from enum import Enum

from graphql import (
    GraphQLArgument, GraphQLEnumType, GraphQLField,
    GraphQLID, GraphQLInt, GraphQLList, GraphQLNonNull,
    GraphQLObjectType, GraphQLSchema, GraphQLString)

import resolvers


# Define the Schema using GraphQL types:


F = GraphQLField
L = GraphQLList
NN = GraphQLNonNull
A = GraphQLArgument

RootType = GraphQLObjectType('Root', lambda: {
    'sub1': F(NN(Sub1Type),
              resolve=resolvers.resolve_sub1,
              ),
})

# InfoType = GraphQLObjectType('Info', lambda: {
#     'this': F(NN(GraphQLInt)),
#     'is': F(NN(GraphQLInt)),
#     'info': F(NN(GraphQLString)),
# })


Sub1Type = GraphQLObjectType('Sub1', lambda: {
    'sub2': F(Sub2Type,
              resolve=resolvers.resolve_sub2,
              args={'some': GraphQLArgument(GraphQLInt), 'arg': GraphQLArgument(GraphQLInt)}),
    'the': F(NN(GraphQLString)),
    'rest': F(NN(GraphQLString)),
    'of': F(NN(GraphQLString)),
    'it': F(NN(GraphQLString)),
})

Sub2Type = GraphQLObjectType('Sub2', lambda: {
    'a': F(NN(GraphQLString)),
    'b': F(NN(GraphQLString)),
    'c': F(NN(GraphQLString)),
})


query_type = GraphQLObjectType('Query', {
    'root': F(NN(RootType),
              args={'id': GraphQLArgument(GraphQLInt), 'info': A(GraphQLString)},
              resolve=resolvers.resolve_root)
})

schema = GraphQLSchema(query_type)