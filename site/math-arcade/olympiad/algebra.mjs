export default {
  id: 'last-counter',
  title: 'The Last Counter',
  subject: 'Invariants',
  level: 'Ascent',
  time: 'Untimed',
  intro: 'Put eight counters on one bench. Spend two to send one to the next bench. Can you make seven trades? Can you predict exactly which positions are reachable on any ring?',
  statement: [
    'Arrange n benches in a clockwise ring, where n ≥ 2. A position lists a nonnegative integer number of counters at each bench. A trade at a bench removes two of its counters and puts one counter at the next bench. A bench needs at least two counters to trade. After the last bench comes the first.',
    'Given any starting position x and proposed finishing position y on the same labelled ring, find a necessary and sufficient test for reaching y from x. Your test must use the two lists of numbers without searching through possible orders of trades. Prove both directions, including the case of an empty target. You may stop at any time or make zero trades.'
  ],
  checkpoints: [
    {
      prompt: 'Three benches A, B, C start at (8, 0, 0). What is the greatest number of trades you can make?',
      answer: '7',
      explanation: 'Trade four times at A, twice at B and once at C. One counter returns to A. Each trade reduces the total by one and leaves at least one counter, so seven is the maximum.'
    },
    {
      prompt: 'Four benches A, B, C, D start at (15, 0, 0, 0). Play until no trade is legal. How many counters remain?',
      answer: '4',
      explanation: 'Give counters at A, B, C and D weights 1, 2, 4 and 8. Trades at A, B and C preserve total weight. A first trade at D would need weight at least 16, but the total before it would still be 15. At the end each bench holds at most one counter, and all four weights are needed to make 15.'
    }
  ],
  hints: [
    'A trade has a direction. How could multiplying the counts at successive benches by 1, 2, 4, 8, … make a trade invisible? What happens at the wrap from the last bench to the first?',
    'Label the benches 0 through n − 1. Let f[i] count the trades at i. A bench spends twice its own trade count and receives the previous bench’s trade count. Try determining the last trade count first.',
    'A list of nonnegative trade counts balances the books. You still have to prove the counters can be spent in a legal order. What happens if you run the proposed trades backwards, starting with y?',
    'In reverse, trade i needs one counter at bench i + 1. If trade i is still owed but bench i + 1 is empty, what does the balance equation at i + 1 imply about the reverse trades still owed there? Follow that implication around the ring.'
  ],
  proof: [
    {
      title: 'Count the trades across the last edge',
      body: 'Number the benches 0 through n − 1. Give a counter at bench i weight 2ⁱ and write W(z) for the sum of these weights in position z. A forward trade at any bench except the last preserves W. At the last bench it spends weight 2ⁿ and creates weight 1. Thus its trade count must be f[n − 1] = (W(x) − W(y))/(2ⁿ − 1).'
    },
    {
      title: 'Recover a unique candidate',
      body: 'Set f[n − 1] to that quotient. For i decreasing from n − 1 to 1, compute f[i − 1] = y[i] − x[i] + 2f[i]. These are the balance equations y[i] = x[i] − 2f[i] + f[i − 1]. The equation for bench 0 also holds, with f[−1] interpreted as f[n − 1]. Indeed, the predicted final position from these counts has weight W(x) − (2ⁿ − 1)f[n − 1] = W(y). It already agrees with y on benches 1 through n − 1, so it agrees on bench 0 as well.'
    },
    {
      title: 'State the test',
      body: 'An empty target is reachable exactly when the start is empty. Every actual trade puts a counter on the next bench. For a nonempty target, accept exactly when every candidate f[i] is a nonnegative integer. Any legal play has these counts by the preceding equations, proving necessity.'
    },
    {
      title: 'Construct a legal order backwards',
      body: 'Start at z = y with r[i] = f[i] reverse trades still owed at each bench. A reverse trade of type i takes one counter from bench i + 1 and puts two at i. Perform any owed reverse trade whose source holds a counter, then decrease its r[i] by one. Throughout, x[j] = z[j] + 2r[j] − r[j − 1], with indices read around the ring. If some r[i] > 0 and no owed trade is legal, then z[i + 1] = 0. Applying the equation at i + 1 gives 2r[i + 1] = x[i + 1] + r[i] > 0. The same reasoning goes all the way around the ring. Every reverse type is owed and every bench is empty. Yet y began nonempty and each reverse trade increases the total by one. This contradiction guarantees a legal move until all debts vanish. The equations then give z = x. Read the moves in reverse order to obtain legal forward play from x to y.'
    }
  ],
  rubric: [
    'Choose weights that identify the exact number of trades from the last bench to the first.',
    'Derive all remaining trade counts, justify the equation at the first bench and test for nonnegative integers.',
    'Settle the empty target separately and prove that any accepted nonempty target has a legal sequence of trades.'
  ],
  transfer: {
    prompt: 'Change the price to three counters for one at the next bench. On a four-bench ring A, B, C, D, start with counters only at A. Finish with exactly two at B and one at D. Every bench must have traded at least once. What is the smallest possible starting pile?',
    answer: '113',
    explanation: 'Use weights 1, 3, 9 and 27. The target weighs 33. A trade at D decreases weight by 80, and trades elsewhere preserve it. At least one trade at D forces a starting pile of at least 113. From 113, trade 37 times at A, 12 at B, 4 at C, once at D and once more at A. The successive positions are (2, 37, 0, 0), (2, 1, 12, 0), (2, 1, 0, 4), (3, 1, 0, 1) and (0, 2, 0, 1).'
  },
  credit: 'Designed for the Atlas Math Olympiad.'
};
