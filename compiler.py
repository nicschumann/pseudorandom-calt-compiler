# -*- coding: utf-8 -*-
# Opentype Pseudorandom CALT Feature Compiler
# ------------------------------------------------------------------------------
# Hacked together by Nic Schumann in December 2020, based on Tal Leming's
# "Quantum" Pseudorandom opentype feature. You can read the idea, context
# and Tal's implementation [here](https://opentypecookbook.com/common-techniques/)
# Towards the bottom of the page. Thanks Tal, for such a thorough intro to
# OpenType Features, and this cool idea.
#
# Given a set of variations for a set of glyphs standard forms in your typeface,
# This script will compile an opentype calt feature that "randomizes" the
# appearance of a glyph across a set of alternates in the typeface
# that you specify.
#
# This script was designed to output a feature that could be copied and pasted
# into Glyphs.app's feature editor (specifically for the calt feature).
# You can also use it from the command line, but you need to specify a complete
# list of the glyphs in your typeface for the script to work properly.
#
# Read on to see how both of these work.
# ------------------------------------------------------------------------------

import random
import functools

# Parameters for Tweaking

# Set a fixed seed, so the results are deterministic.
# If you want a different random partition of your font,
# set this seed from `0` to some other number.
random.seed(0)

# The DEPTH parameter controls the distance of the lookahead
# the feature will use. The greater the depth, the longer-range
# the feature triggers will be. Conversely, the greater the depth,
# The more work the opentype renderer has to do to set the text...
DEPTH = 10

# Tal's technique depends on randomly partitioning the entire character set
# into 2 partitions. These different partitions are "pseudo-random seeds", which
# trigger different alternates to be substuted in, in a fairly random-seeming pattern.
# This technique avoids the cycle affect that you see with rotation based substitutions;
# If you type 'aaaaa', you'll see a fairly random looking set of alternates render, rather
# than what you'd see with a rotation based technique: alt1, alt2, alt3, alt1, etc.
#
# Tal's example uses two partitions, but you can experiment with more than two,
# as well. Increasing the number of partitions changes the texture of
# the randomness that's created.
PARTITIONS = 2

# Base Glyph names.
base = ["a", "g", "l", "u"]
# Variation 1. Must be the same length as base. The alternate for
# base[i] should be at position variation_1[i]. same goes for
# all the other variations.
variation_1 = ["abreve", "gdotaccent","lslash", "ubreve"]
# Variation 2.
variation_2 = ["acircumflex", "gcommaaccent", "lcaron", "uring"]
# variation 3.
variation_3 = ["aacute", "gbreve", "ldot", "uacute"]

# End of Parameters for Tweaking


# This script is designed for use in Glyphs.app's macro window. However, it's
# easy to use it outside of Glyphs.app. Just replace the value of all_exporting_glyphs
# with a python list of the all the glyph names in your typeface that export. In other words,
# something like ["A", "B", "C"] and so on.
all_exporting_glyphs = map( lambda g: g.name, filter(lambda g: g.export, Glyphs.font.glyphs))


# If you add more variations than the three set above (which should work fine),
# You should add the additional arrays to the end of this transitions array.
transitions = [base, variation_1, variation_2, variation_3]


def generate_class_definition_kvpair((i, glyphs)):
	return ("@transformation%i" % i, "[%s]" % " ".join(glyphs))

def generate_state_definitions( transitions ):
	return map(generate_class_definition_kvpair, enumerate(transitions))

def generate_permutation_definitions_from_states(states):
	classes = map(lambda p: p[0], states)
	return map(lambda i: ("@state%s" % i, "[%s]" % " ".join(classes[i:] + classes[:i])), range(len(classes)))

def generate_charset_partitions(glyphs, k=2):
	partitions = map(lambda i: ("@partition%i" % i, []), range(k))

	for g in range(len(glyphs) // k):
		for _, elements in partitions:
			elements.append(glyphs.pop(random.randrange(len(glyphs))))

	return map(lambda p: (p[0], "[%s]" % " ".join(sorted(p[1]))), partitions)

def generate_all(glyphs):
	return [("@All", "[%s]" % " ".join(glyphs))]

def generate_skip():
	# Assumes you have an @All class available
	return [("@skip", "[@All]")]

def generate_lookups(permutations, partitions, skip, depth=1):
	lookups = []
	p_names = map(lambda p: p[0], permutations) + [permutations[0][0]]
	p_map = map(lambda i: (p_names[i], p_names[i + 1]), range(len(p_names) - 1))

	for d in range(depth):
		lookups.append([])
		for i, partition in enumerate(reversed(partitions)):
			lookups[d].append((
				"skip" + str(d) + '_partition' + str(i),
				partition[0],
				(skip[0][0],) * d,
				p_map[i % len(p_map)][0],
				p_map[i % len(p_map)][1]
			))

	return lookups

def compile_class_definition(data, indent=""):
	return functools.reduce(lambda a, b: a + indent + "%s = %s;\n" % b, data, "")

def compile_lookup_definitions(data, indent=""):
	def compile_lookup(lookup):
		name, partition, skips, from_state, to_state = lookup
		definition  = indent + "lookup %s {\n" % name
		definition += indent + "\tsub %s %s %s' by %s;\n" % (partition, " ".join(skips), from_state, to_state)
		definition += indent + "} %s;\n\n" % name
		return definition

	return "\n\n".join(map(lambda lookup_set: functools.reduce(lambda a, b: a + compile_lookup(b), lookup_set, ""), reversed(data)))

## Compile Feature Program
def compile_feature_body(transitions, all_glyphs, depth=DEPTH, partitions=PARTITIONS, indent=""):
    S = generate_state_definitions(transitions)
    T = generate_permutation_definitions_from_states(S)
    P = generate_charset_partitions(all_exporting_glyphs, k=PARTITIONS)
    ALL = generate_all(all_exporting_glyphs)
    SKIP = generate_skip()
    LOOKUPS = generate_lookups(T, P, SKIP, depth=DEPTH)

    program  = "\n".join([
        indent + compile_class_definition(S, indent=indent),
        compile_class_definition(T, indent=indent),
        compile_class_definition(P, indent=indent),
        # compile_class_definition(ALL), # Uncomment if you need the @All class
        compile_class_definition(SKIP, indent=indent),
        compile_lookup_definitions(LOOKUPS, indent=indent)])

    return program

# if you want to generate a
def compile_feature(transitions, all_glyphs, depth=DEPTH, partitions=PARTITIONS, indent=""):
    program  = "feature calt {\n\n"
    program += compile_feature_body(transitions, all_glyphs, depth=DEPTH, partitions=PARTITIONS, indent=indent + "\t")
    program += "\n} calt;"

    return program

# Full feature definitions are not needed for glyphs.app's feature editor
# If you want to compile a full feature defintiion, change the function
# below from `compile_feature_body` to `compile_feature`
print(compile_feature_body(transitions, all_exporting_glyphs))
