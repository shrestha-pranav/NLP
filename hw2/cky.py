
# coding: utf-8

# In[1]:


import math
import sys
from collections import defaultdict
import itertools
from grammar import Pcfg


# In[2]:


### Use the following two functions to check the format of your data structures in part 3 ###
def check_table_format(table):
    """
    Return true if the backpointer table object is formatted correctly.
    Otherwise return False and print an error.  
    """
    if not isinstance(table, dict): 
        sys.stderr.write("Backpointer table is not a dict.\n")
        return False
    for split in table: 
        if not isinstance(split, tuple) and len(split) ==2 and           isinstance(split[0], int)  and isinstance(split[1], int):
            sys.stderr.write("Keys of the backpointer table must be tuples (i,j) representing spans.\n")
            return False
        if not isinstance(table[split], dict):
            sys.stderr.write("Value of backpointer table (for each span) is not a dict.\n")
            return False
        for nt in table[split]:
            if not isinstance(nt, str): 
                sys.stderr.write("Keys of the inner dictionary (for each span) must be strings representing nonterminals.\n")
                return False
            bps = table[split][nt]            
            if isinstance(bps, str): # Leaf nodes may be strings
                continue 
            if not isinstance(bps, tuple):
                sys.stderr.write("Values of the inner dictionary (for each span and nonterminal) must be a pair ((i,k,A),(k,j,B)) of backpointers. Incorrect type: {}\n".format(bps))
                return False
            if len(bps) != 2:
                sys.stderr.write("Values of the inner dictionary (for each span and nonterminal) must be a pair ((i,k,A),(k,j,B)) of backpointers. Found more than two backpointers: {}\n".format(bps))
                return False
            for bp in bps: 
                if not isinstance(bp, tuple) or len(bp)!=3:
                    sys.stderr.write("Values of the inner dictionary (for each span and nonterminal) must be a pair ((i,k,A),(k,j,B)) of backpointers. Backpointer has length != 3.\n".format(bp))
                    return False
                if not (isinstance(bp[0], str) and isinstance(bp[1], int) and isinstance(bp[2], int)):
                    print(bp)
                    sys.stderr.write("Values of the inner dictionary (for each span and nonterminal) must be a pair ((i,k,A),(k,j,B)) of backpointers. Backpointer has incorrect type.\n".format(bp))
                    return False
    return True

def check_probs_format(table):
    """
    Return true if the probability table object is formatted correctly.
    Otherwise return False and print an error.  
    """
    if not isinstance(table, dict): 
        sys.stderr.write("Probability table is not a dict.\n")
        return False
    for split in table: 
        if not isinstance(split, tuple) and len(split) ==2 and isinstance(split[0], int) and isinstance(split[1], int):
            sys.stderr.write("Keys of the probability must be tuples (i,j) representing spans.\n")
            return False
        if not isinstance(table[split], dict):
            sys.stderr.write("Value of probability table (for each span) is not a dict.\n")
            return False
        for nt in table[split]:
            if not isinstance(nt, str): 
                sys.stderr.write("Keys of the inner dictionary (for each span) must be strings representing nonterminals.\n")
                return False
            prob = table[split][nt]
            if not isinstance(prob, float):
                sys.stderr.write("Values of the inner dictionary (for each span and nonterminal) must be a float.{}\n".format(prob))
                return False
            if prob > 0:
                sys.stderr.write("Log probability may not be > 0.  {}\n".format(prob))
                return False
    return True


# In[3]:


getHead = lambda x, grammar: set(rule[0] for rule in grammar.rhs_to_rules[x])
cartesian = lambda x, y: set([(i, j) for i in x for j in y])

class CkyParser(object):
    """ A CKY parser. """
    def __init__(self, grammar): 
        """ Initialize a new parser instance from a grammar. """
        self.grammar = grammar

    def getHead(self, x):
        return [rule[0] for rule in self.grammar.rhs_to_rules[x]]

    def is_in_language(self,tokens):
        """
        Membership checking. Parse the input tokens and return True if 
        the sentence is in the language described by the grammar. Otherwise
        return False
        """
        n = len(tokens)
        s = [[None]*(n+1) for i in range(n+1)]

        # Initialization
        for i in range(n):
            s[i][i+1] = set(self.getHead((tokens[i], )))

        # For each stage of the process
        for length in range(2, n+1):
            
            # For each generation of s[i][j]
            for i in range(n-length+1):
                j = i+length
                s[i][j] = set([])
                
                # Generate all posibilities of s[i][k], s[k][j]: i<k<j
                for k in range(i+1, j):

                    for pair in cartesian(s[i][k], s[k][j]):
                        s[i][j] = s[i][j].union(set(self.getHead(pair)))
        
        # Check if the entire sentence was generated by the parse
        if self.grammar.startsymbol in s[0][n]:
            return True

        return False
       
    def parse_with_backpointers(self, tokens):
        n = len(tokens)
        table = dict()
        probs = dict()
        
        s = [[None]*(n+1) for i in range(n+1)]

        # Initialization
        for i in range(n):                
            s[i][i+1] = self.getHead((tokens[i], ))
            probs[(i, i+1)] = dict()
            table[(i, i+1)] = dict()
            
            for (lhs, rhs, prob) in self.grammar.rhs_to_rules[(tokens[i],)]:
                prob = math.log(prob)
                
                if lhs not in probs[(i,i+1)] or                     prob > probs[(i,i+1)][lhs]:
                    table[(i,i+1)][lhs] = tokens[i]
                    probs[(i,i+1)][lhs] = prob
                    
        # For each stage of the process
        for length in range(2, n+1):
            
            
            # For each generation of s[i][j]
            for i in range(n-length+1):
                j = i+length
                s[i][j] = set([])
                
                probs[(i,j)] = dict()
                table[(i,j)] = dict()
                
                # Generate all posibilities of s[i][k], s[k][j]: i<k<j
                for k in range(i+1, j):
                    # Generate each pair
                    for B in table[(i, k)].keys():
                        for C in table[(k,j)].keys():

                            for(lhs, rhs, prob) in self.grammar.rhs_to_rules[(B,C)]:
                                prob = math.log(prob) + probs[(i,k)][B] + probs[(k,j)][C]
                                
                                if lhs not in probs[(i,j)] or                                     prob > probs[(i,j)][lhs]:
                                    table[(i,j)][lhs] = ((rhs[0], i, k), (rhs[1], k, j))
                                    probs[(i,j)][lhs] = prob
                                    
                    for pair in cartesian(s[i][k], s[k][j]):
                        s[i][j] = s[i][j].union(set(self.getHead(pair)))
        
        # Check if the entire sentence was generated by the parse
        return table, probs


# In[4]:


def get_tree(chart, i, j, nt): 
    """
    Return the parse-tree rooted in non-terminal nt and covering span i,j.
    """
    rhs = chart[(i,j)][nt]
    if isinstance(rhs, str):
        return (nt, rhs)
    else:
        return (
            nt,
            get_tree(chart, rhs[0][1], rhs[0][2], rhs[0][0]),
            get_tree(chart, rhs[1][1], rhs[1][2], rhs[1][0]))


# In[8]:


if __name__ == "__main__":
    
    with open('atis3.pcfg','r') as grammar_file: 
        grammar = Pcfg(grammar_file) 
        parser = CkyParser(grammar)
        toks =['flights', 'from','miami', 'to', 'cleveland','.'] 
        print(parser.is_in_language(toks))
        
        table,probs = parser.parse_with_backpointers(toks)
        
        assert check_table_format(table)
        assert check_probs_format(probs)
        
        print(get_tree(table, 0, len(toks), grammar.startsymbol))


# In[6]:


def print_tree(s):
    print(" ", list(range(len(s))))
    for n, row in enumerate(s):
#         tmp = [str(i) if m > n else "" for m,i in enumerate(row) if m>0]
#         tmp = [i.ljust(30) for i in tmp]
        print(n, row[1:])


# In[7]:


def print_table(s, n):
    x = [[None]*n for i in range(n)]
    for i in range(n):
        for j in range(i, n):
            x[i][j] = s.get((i,j), None)
    
    for i, row in enumerate(x):
        print()
        for j, data in enumerate(row):
#             if i>=j: continue
            print((i, j), data)

