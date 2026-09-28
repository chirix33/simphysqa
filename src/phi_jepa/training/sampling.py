"""Pair-uniform sampling without altering any per-pair training objective."""
import random


def fixed_pair_batches(pairs,batch_size,updates,seed):
    """Shuffle cycles of all question-conditioned pairs, carrying short tails.

    Every update has the same number of equally weighted pairs. A pair repeated
    across question contexts remains a distinct supervised example.
    """
    if not pairs or batch_size<1 or updates<1: raise ValueError('positive_sampler_sizes_required')
    rng=random.Random(seed); pending=[]; cursor=0
    for _ in range(updates):
        while len(pending)-cursor<batch_size:
            pending=pending[cursor:]; cursor=0; cycle=list(range(len(pairs))); rng.shuffle(cycle); pending.extend(cycle)
        chosen=pending[cursor:cursor+batch_size]; cursor+=batch_size
        yield chosen


def chronological_sequence_order(sequences,updates,seed):
    """Choose whole sequences proportional to length; retain chronological state.

    The unchanged mean transition loss then gives every question-conditioned
    pair equal expected gradient weight: (L/N)*(1/L)=1/N. This is not uniform
    sequence weighting. Actual per-pair exposure must still be recorded.
    """
    if not sequences or any(not s for s in sequences): raise ValueError('nonempty_sequences_required')
    return random.Random(seed).choices(range(len(sequences)),weights=[len(s) for s in sequences],k=updates)
