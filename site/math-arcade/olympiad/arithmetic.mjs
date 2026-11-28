export default {
  id: 'shifted-squares',
  title: 'The shifted squares',
  subject: 'Algebra',
  level: 'Summit',
  time: 'Untimed',
  intro: 'Two machines square an integer. One also adds a fixed shift. Which polynomials can divide their own outputs from both machines?',
  statement: [
    'Choose a nonzero integer c and a nonconstant monic polynomial P with integer coefficients. Monic means that its leading coefficient is 1. For every positive integer n with P(n) ≠ 0, require P(n) to divide both P(n²) and P(n² + c).',
    'Determine every possible pair (c, P). Prove that your list is complete and that every member passes both tests. As an extension, decide whether the list changes if both tests need to hold for only infinitely many positive integers n.',
    'You may use the fundamental theorem of algebra in the form that a degree-d complex polynomial has d roots when multiplicities are counted.'
  ],
  checkpoints: [
    { prompt: 'A nonzero root returns to an earlier value after repeated squaring. What must its absolute value be?', answer: '1', explanation: 'Some iterates satisfy z^(2ʲ) = z^(2ᵏ) with j < k. Dividing gives a positive power of z equal to 1.' },
    { prompt: 'Every root and both of its images lie in the closed unit disk. What is the largest possible absolute value of the shift c?', answer: '2', explanation: 'The points z² and z² + c are at distance |c|. The unit disk has diameter 2, and c = −2 actually occurs for P(x) = x² − 1.' },
    { prompt: 'For c = −1, suppose P(x) = (x + 1)³(x − 1)⁴xᵈ. What is the greatest d for which the two tests hold?', answer: '6', explanation: 'At 0 the shifted map hits −1 to order 2, so d ≤ 2 × 3. The simple preimages at 1 and −1 require 3 ≤ 4 ≤ d. Thus d = 6 works.' }
  ],
  hints: [
    'Divide P(x² + c) by P(x) as polynomials. How large can the remainder at n be compared with P(n) as n tends to infinity? Apply the same argument with shift zero.',
    'After lifting the divisibility to polynomials, follow a complex root under repeated squaring. Both z² and z² + c must now belong to the set consisting of 0 and the unit circle.',
    'When |c| = 1, find the intersection of two unit circles with centres one unit apart. A point in that intersection is only a candidate: both of its next images must still be allowed.',
    'Keep a multiplicity on each surviving root. Usually composition preserves the multiplicity of its image. At the input 0, the maps x² and x² + c double it.'
  ],
  proof: [
    { title: 'Turn the integer tests into polynomial identities', body: 'For f(x) = x² or x² + c, divide P(f(x)) by the monic P(x). The quotient and remainder R have integer coefficients, and R is zero or has smaller degree than P. At each tested n, the nonzero integer P(n) divides R(n). For all sufficiently large n, |R(n)| < |P(n)|. Thus R vanishes at infinitely many n and is identically zero. The converse follows by evaluating the integer-coefficient quotient. This already answers the extension: infinitely many simultaneous successes give the very same identities.' },
    { title: 'Trap the roots', body: 'Let S be the finite, nonempty set of complex roots of P. Divisibility forces both z² and z² + c into S whenever z is in S. Repeated squaring of any nonzero root must revisit an earlier value, so that root is a root of unity. Hence every root is either 0 or has absolute value 1. The distance between z² and z² + c is |c| ≤ 2. Only −2, −1, 1 and 2 remain.' },
    { title: 'Multiplicity is the second test', body: 'Write m(z) for the multiplicity of z in P. At a root z and for either map f, the multiplicity of z in P(f(x)) is m(f(z)) times the order of the zero of f(x) − f(z) at x = z. Since f(x) − f(z) = (x − z)(x + z), this factor is 1 if z ≠ 0 and 2 if z = 0. Consequently a root set closed under both maps gives divisibility precisely when m(z) is at most that product for every root and both maps. This criterion proves sufficiency as well as necessity, since it counts every linear factor of P.' },
    { title: 'Shifts of size two', body: 'Two points in the closed unit disk can be two units apart on a horizontal line only at the endpoints −1 and 1. For c = 2 we must have z² = −1 for every root z. But −1 is then itself a root and its shifted image is 3, impossible. For c = −2 we must have z² = 1, and its two images 1 and −1 both occur. Both roots are nonzero, and each maps to 1 by squaring and to −1 by shifted squaring. Their multiplicities must be equal. Exactly P(x) = (x² − 1)ᵏ, with k any positive integer, works.' },
    { title: 'The negative unit shift', body: 'For c = −1 let t = z². If t is neither 0 nor 1, both t and t − 1 have absolute value 1. Subtracting their squared absolute values gives Re(t) = 1/2, and then Re(t²) = −1/2. But t is itself a root, so t² − 1 must be a root, although |t² − 1|² = 3. Therefore z² is 0 or 1. The only roots are 0, −1 and 1, and all three occur because 0 goes to −1, −1 goes to 1, and 1 goes to 0 under appropriate maps. Put a = m(−1), b = m(1), d = m(0). At −1 and 1 the images are 1 and 0. At 0 they are 0 and −1, each reached to order 2. The full criterion reduces to a ≤ b ≤ d ≤ 2a. All polynomials P(x) = (x + 1)ᵃ(x − 1)ᵇxᵈ with positive integers satisfying these inequalities work.' },
    { title: 'The positive unit shift', body: 'For c = 1, zero cannot occur: its shifted image is 1 and the shifted image of 1 is 2. For any root z, t = z² and t + 1 now both have absolute value 1, giving Re(t) = −1/2. Thus t is one of the two nonreal cube roots of unity, say ω and ω². The four possible z are ω, ω², −ω and −ω². They are exactly the roots of x⁴ + x² + 1. From any one of them, squaring reaches one of ω and ω², which squaring interchanges. Shifted squaring from these two reaches the other pair, using 1 + ω = −ω² and 1 + ω² = −ω. Hence each candidate reaches every other, and the four-point set is closed under both maps. Multiplicities cannot decrease along these steps, so they all agree. Exactly P(x) = (x⁴ + x² + 1)ᵏ with k any positive integer works. Together with the two negative shifts this exhausts the list.' }
  ],
  rubric: [
    'Justify the passage from divisibility at integers to divisibility in the polynomial ring, including the variant with infinitely many test values.',
    'Prove the unit-circle obstruction, bound c, and check that candidate roots survive further iterations of both maps.',
    'Track multiplicities at every surviving root, including the exceptional input 0, and obtain all three families with the correct exponent restrictions.',
    'Verify that all listed polynomials pass both tests and that each excluded shift or root has a demonstrated obstruction.'
  ],
  transfer: {
    prompt: 'How many different admissible pairs (c, P) have P of degree exactly 36?',
    answer: '17',
    explanation: 'For c = −1, write 36 = a + b + d with a ≤ b ≤ d ≤ 2a. Then 8 ≤ a ≤ 12 and max(a, 36 − 3a) ≤ b ≤ floor((36 − a)/2). The five values of a give 3, 5, 4, 2 and 1 choices, totalling 15. For c = −2 there is one power of the quadratic, and for c = 1 one power of the quartic. The total is 17.'
  },
  credit: 'Designed for the Atlas Math Olympiad. Techniques include polynomial division, finite root orbits and multiplicity under composition.'
};
