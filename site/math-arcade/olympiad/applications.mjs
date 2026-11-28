export default {
  'last-counter': {
    title: 'Which ticket bundle can the club promise?',
    scenario: 'A games club is trying a three-colour ticket exchange. Two red tickets buy one blue, two blue buy one gold, and two gold buy one red. A visitor has eight red tickets. The organiser wants to advertise one of two four-ticket bundles.',
    question: 'Which bundle can the visitor obtain without borrowing tickets: two red, one blue and one gold, or two red and two blue? Predict whether either, both or neither is possible.',
    model: [
      'The first bundle is possible. Make three red exchanges to get two red and three blue. Exchange two of those blue for one gold. The visitor now has two red, one blue and one gold.',
      'Give red, blue and gold tickets weights 1, 2 and 4. The first two exchanges preserve weight, and a gold exchange reduces weight by 7. The starting weight is 8. The second bundle weighs 6, a reduction of 2, so no legal exchange sequence can produce it.'
    ],
    limitation: 'The conclusion depends on the club enforcing the three rates exactly. A free ticket, a reverse exchange or a loan changes which promises it can keep.',
    investigate: 'Use three labelled cups and paper tickets. Start with eight red, record the counts after each trade, and check the weight after each step. Repeat from nine red and try to build the two advertised bundles again.'
  },
  'three-turn-triangle': {
    title: 'Will a map icon fit its printed box?',
    scenario: 'A designer builds a triangular map icon by applying the problem’s three midpoint passes. The original right triangle has horizontal and vertical legs of 120 mm and 90 mm. The finished icon must keep the same orientation and exactly fill a 10 mm by 7.5 mm box.',
    question: 'After settings 1/2 and 1/6, which signed third setting should the designer use? Predict the final length of the sloping edge before measuring it.',
    model: [
      'Choose −1/3. The proof gives a scale of +1/12 about the original centroid. Every edge vector keeps its direction and becomes one twelfth as long. The legs become 10 mm and 7.5 mm, which gives the required bounding box.',
      'The original sloping edge measures 150 mm by Pythagoras. Its predicted final length is 12.5 mm. The centroid also stays fixed, so it gives the designer a second check on placement.'
    ],
    limitation: 'The dimensions describe the triangle’s vertex positions. A thick outline can extend beyond them, and rounding after each pass can move the final vertices.',
    investigate: 'Draw the three passes on graph paper or in a drawing tool, retaining the cyclic labels. Measure the final three sides and the shift of the centroid. Repeat with a scalene triangle of your own and compare each measured ratio with 1/12.'
  },
  'shifted-squares': {
    title: 'Can a logger regroup time bins without splitting one?',
    scenario: 'A classroom sensor logger groups readings into bins that start from a common time zero. In integer mode n ≥ 2, each bin is P(n) = n² − 1 ticks wide. A proposed update changes the mode to n² or n² − 2. The designer wants every new bin to contain a whole number of complete old bins.',
    question: 'At n = 3, predict how many old bins fit after each update. Would replacing the second update by n² + 2 also work for every mode?',
    model: [
      'An old bin is 8 ticks wide. The new modes 9 and 7 give widths 80 and 48, so one new bin holds 10 or 6 old bins. For any n ≥ 2 the two new widths factor as (n² − 1)(n² + 1) and (n² − 1)(n² − 3). Each ratio is a positive integer.',
      'The proposed +2 update also passes at n = 3, but fails at n = 4. The old width is 15 and the new width is 18² − 1 = 323. A boundary at tick 323 cuts the old bin from tick 315 to tick 330.'
    ],
    limitation: 'Divisibility settles boundary alignment for a shared time zero and exact integer ticks. It cannot recover readings missing from an old bin or align clocks with different starting offsets.',
    investigate: 'In a spreadsheet, list n from 2 to 10. For each update divide the new width by the old and record the remainder. Then shift the new bin origin by one tick and mark its first boundary on a timeline to see which prediction depended on the shared origin.'
  },
  'two-missing-lamps': {
    title: 'Which fourteen switch tests should the lab run?',
    scenario: 'A prototype has five on/off switches A through E. The lab can run 14 of 32 settings. It wants complete eight-run experiments in which three independent toggle actions can each be on or off. An action may flip several switches together. Count each distinct eight-setting experiment once.',
    question: 'Schedule I runs every setting with E off except 00000 and 11110, writing switches in ABCDE order. Schedule II replaces 00110 in that list with 00111. Which schedule preserves more complete experiments? Does the winner ever exercise switch E in its on position?',
    model: [
      'Schedule I attains the theorem’s maximum of seven. Within the 16 settings with E off, each eight-run experiment is one parity condition on A through D. To avoid both omitted settings, the parity must agree on them and we choose the opposite value. Seven nonempty subsets of the four switches have even size, giving seven such conditions.',
      'Schedule II leaves three settings missing from the E-off group. To exclude all three, a nonempty subset must have even size and contain either both C and D or neither. Exactly three qualify: AB, CD and ABCD. The single E-on setting cannot complete another experiment, since any affine cube on which E varies has four settings of each kind. Schedule II therefore preserves three experiments.'
    ],
    limitation: 'A count of complete experiments measures this particular design objective. Schedule I never turns E on, so a fault that occurs only with E on can escape all fourteen tests.',
    investigate: 'List both schedules in a spreadsheet and model a warning that appears exactly when E is on and A is off. Run both lists and count the warnings. Compare that observation with the seven-versus-three prediction, then choose a schedule for a lab whose priority is finding that warning.'
  }
};
