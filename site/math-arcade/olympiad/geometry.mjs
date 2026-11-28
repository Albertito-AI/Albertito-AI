export default {
  id: 'three-turn-triangle',
  title: 'The Three-Turn Triangle',
  subject: 'Geometry',
  level: 'Summit',
  time: 'Untimed',
  intro: 'Move three side midpoints at right angles to their sides. Can a third move restore the shape of every starting triangle?',
  statement: [
    'Start with any labelled, noncollinear triangle ABC in the plane. A pass has a real setting s. To construct A′, start at the midpoint of BC, turn the arrow from B to C anticlockwise through 90°, multiply that arrow by s, and add it to the midpoint. Construct B′ from the arrow from C to A and C′ from the arrow from A to B in the same way. A negative setting reverses the turned arrow. Keep these cyclic labels on every pass, even if the orientation changes. A zero-length arrow contributes zero displacement.',
    'Use settings 1/2, 1/6 and t in that order, always working on the latest triple. Let G be the centroid of the original triangle. Prove that every pass preserves G. Find the unique real t for which, for every starting triangle, the three final arrows from G are all the same scalar multiple r of their corresponding original arrows from G. Determine r and prove the uniqueness of t.',
    'Now replace the first two settings by any real numbers a and b. Determine exactly when there is one possible third setting, when there is none, and when every third setting works. Allow r = 0 in this classification, meaning that all three final vertices coincide at G.'
  ],
  diagram: 'geometry.svg',
  diagramAlt: 'First pass at setting one half. A is at (0,0), B at (8,0) and C at (0,4). From the midpoint M at (4,2), a perpendicular arrow ends at A′ at (2,−2). The arrow on BC points from B towards C.',
  checkpoints: [
    { prompt: 'In the illustrated triangle let A = (0,0), B = (8,0), C = (0,4). Reverse the pictured setting to s = −1/2. What is the new y-coordinate of A′?', answer: '6', explanation: 'The arrow from B to C is (−8,4). Its anticlockwise quarter-turn is (−4,−8). Subtract half of that vector from the midpoint (4,2) to reach (6,6).' },
    { prompt: 'Write J for the anticlockwise quarter-turn. For vectors u + v + w = 0 define K(u,v,w) = (J(w−v), J(u−w), J(v−u)). Applying K twice gives m times the original triple. What integer is m?', answer: '3', explanation: 'The first component after two applications is J(J(v−u) − J(u−w)) = −v + 2u − w = 3u. Cycling the letters gives the other two components.' },
    { prompt: 'Use the setting that works after 1/2 and 1/6. If the original distance GA is 60 units, how far is the final vertex with label A from G?', answer: '5', explanation: 'The three passes scale each position vector from G by 1/12, so a distance of 60 becomes 5.' }
  ],
  hints: [
    'The three directed side arrows form a closed walk. Add the three midpoint positions and then add the three perpendicular displacements.',
    'Work from G as origin. If u, v and w are the vertex vectors, their sum vanishes. The midpoint opposite u therefore has vector −u/2. Use K from the second checkpoint to write one whole pass as a single operation.',
    'Once K² is known, two passes act as a multiple of the identity plus a multiple of K. Multiply by the third pass and look for the coefficient of K.',
    'For necessity, try the illustrated right triangle. Its arrow from G to A is parallel to (2,1), while the perpendicular to BC is parallel to (1,2). A nonzero multiple of the second direction cannot be absorbed into a multiple of the first.'
  ],
  proof: [
    { title: 'Follow the centroid', body: 'Write J for the anticlockwise quarter-turn of a vector, so J is linear and J² sends x to −x. The three side midpoints sum, as position vectors, to A + B + C. The sum of the three added arrows is sJ((C−B) + (A−C) + (B−A)) = 0. The average of the new positions is therefore G on every pass.' },
    { title: 'Turn the side differences twice', body: 'Place the origin at G and write X = (u,v,w) for the centred vertex vectors. Then u + v + w = 0. The midpoint opposite u is −u/2. With KX = (J(w−v), J(u−w), J(v−u)), a pass sends X to TₛX = (−I/2 + sK)X, where I leaves X fixed. The components of KX sum to zero, so the same formula applies again. The first component of K²X is J(J(v−u) − J(u−w)) = 2u − v − w = 3u. The other components are 3v and 3w by cyclic relabelling. Hence K² = 3I on centred triples.' },
    { title: 'Find the third setting', body: 'The passes with settings 1/2 and 1/6 together give (−I/2 + K/6)(−I/2 + K/2) = I/2 − K/3. After the third pass the operation is (−1/4 − t)I + (1/6 + t/2)K. Taking t = −1/3 cancels the K term. The coefficient of I becomes 1/12, so each final vertex lies one twelfth of the way from G to its original vertex.' },
    { title: 'Prove that cancellation is necessary', body: 'Use A = (0,0), B = (8,0), C = (0,4). Here G = (8/3,4/3), so u = (−8/3,−4/3), while the first component of KX is J(C−B) = (−4,−8). These two vectors are not parallel. If an operation αI + βK scales the arrows from G for every starting triangle, its first component on this example must be parallel to u or zero. This forces β = 0. In particular the setting −1/3 found above is unique.' },
    { title: 'Classify all first and second settings', body: 'For settings a and b, the first two passes give (1/4 + 3ab)I − ((a+b)/2)K. After setting t, the coefficient of K is (a+b + t(1+12ab))/4. The preceding triangle shows that it must vanish, and its vanishing is sufficient. If 1+12ab ≠ 0, the unique setting is t = −(a+b)/(1+12ab). If 1+12ab = 0 and a+b ≠ 0, there is no setting. If both are zero, every t works. In the last case the first two passes already give the zero operation, so every vertex has reached G before the third pass.' }
  ],
  rubric: [
    'Show that the three added arrows sum to zero and that the three midpoint positions have the original centroid.',
    'Represent a pass on centred vectors and prove the identity K² = 3I, or give a geometric argument with the same consequence.',
    'Derive t = −1/3 and r = 1/12, and establish why no other third setting works for every triangle.',
    'Give the full classification for arbitrary a and b, including both possibilities when 1+12ab vanishes.'
  ],
  transfer: { prompt: 'A machine has first settings 1 and 2. Write its unique restoring setting as a reduced fraction with positive denominator. What is that denominator?', answer: '25', explanation: 'The equation is 3 + 25t = 0, so t = −3/25. Since 3 and 25 are coprime, the denominator is 25.' },
  credit: 'Designed for the Atlas Math Olympiad.'
};
