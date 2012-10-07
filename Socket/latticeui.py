#!/usr/bin/env python

# Copyright (c) 2007 Carnegie Mellon University.
#
# You may modify and redistribute this file under the same terms as
# the CMU Sphinx system.  See
# http://cmusphinx.sourceforge.net/html/LICENSE for more information.
#
# Briefly, don't remove the copyright.  Otherwise, do what you like.

"""
Model and view/controller classes for a touchscreen ASR error
correction implementation.
"""

__author__ = "David Huggins-Daines <dhuggins@cs.cmu.edu>"

# System imports
import pygtk
pygtk.require('2.0')
import gtk
import gobject
import pango
import sys
import math
import sphinxbase
import pocketsphinx

def is_real_word(w):
    if w.startswith('++'):
        return False
    if w.startswith('<'):
        return False
    return True

class LatticeWord(object):
    """Word in a LatticeModel."""
    __slots__ = ['sym', 'start', 'end', 'prob', 'base_prob']
    def __init__(self, sym, start, end, prob=0):
        """
        Initialize a LatticeWord.

        @param sym: Word string
        @type sym: string
        @param start: Start time
        @type start: int
        @param end: End time
        @type end: int
        @param prob: Posterior log-probability
        @type prob: float
        """
        self.sym = sym        #: Word string
        self.start = start    #: Start time of word
        self.end = end        #: End time of word
        self.prob = prob      #: Posterior log-probability of word
        self.base_prob = prob  #: ASR-derived posterior log-probability

    def set_prob(self, prob):
        """
        Update the posterior probability of this word

        LatticeWords distinguish between their inherent posterior
        probability, which is derived purely from ASR results, and
        their effective posterior probability, which can be modified
        based on user input.

        @param prob: New posterior log-probability
        @type prob: float
        """
        self.prob = prob

    def reset_prob(self):
        """
        Reset the posterior probability to the inherent value
        """
        self.prob = self.base_prob

class LatticeCloud(object):
    """
    An expandable "cloud" of hypothesized words.

    A cloud has two dimensions: time and beam width.  The cloud
    contains all words which fall inside the specified start and
    end points and are within a certain ratio from the best
    posterior probability.
    """
    def __init__(self, dag, start, end, beam=0.0):
        """
        Create a LatticeCloud object.

        @param dag: Word lattice to initialize this object with.
        @type dag: lattice.Dag
        @param start: Start time for this cloud.
        @type start: int
        @param end: End time for this cloud.
        @type end: int
        @param beam: Beam width (log-probability ratio).
        @type beam: float
        """
        self.dag = dag     #: DAG
        self.beam = beam   #: Beam width of cloud
        self.set_time_extents(start, end)

    def set_beam(self, beam):
        """
        Set the beam width for the cloud.

        @param beam: Beam width (log-probability ratio).
        @type beam: float
        """
        self.beam = beam   #: Beam width of cloud

    def set_time_extents(self, start, end):
        """
        Set the time extents for the cloud.

        @param start: Start time for this cloud.
        @type start: int
        @param end: End time for this cloud.
        @type end: int
        """
        self.start = start #: Start time of cloud
        self.end = end     #: End time of cloud
        self.max  = -10000 #: maximum posterior probability
        self.min  = 0      #: minimum posterior probability
        # Scan the DAG to get all nodes in the given range
        self.nodes = []    #: all nodes in this span
        seen = set()
        for node in self.dag.nodes(self.start, self.end):
            if not is_real_word(node.baseword):
                continue
            if node.baseword in seen:
                continue
            seen.add(node.baseword)
            best_edge = None
            for x in node.exits():
                # Look for edges fully contained in this region.  Note
                # that end frame numbers are inclusive, whereas
                # self.start and self.end are not.
                if x.ef >= self.start and x.ef < self.end:
                    # Look for the highest and lowest posterior probability
                    if best_edge == None or x.prob > best_edge[1]:
                        best_edge = (x.ef + 1, x.prob)
                        if x.prob > self.max:
                            self.max = x.prob
                        if x.prob < self.min:
                            self.min = x.prob
            if best_edge:
                self.nodes.append(LatticeWord(node.baseword, node.sf, *best_edge))
            elif len(tuple(node.exits())) == 0:
                # This is often the case for the last word
                self.nodes.append(LatticeWord(node.baseword, node.sf, node.lef + 1, 0))

    def __iter__(self):
        """Return an iterator over the words in this cloud."""
        for node in self.nodes:
            if node.prob >= self.max - self.beam:
                yield node

class LatticeModel(object):
    """
    Model of a word lattice obtained from speech recognition, along
    with a possibly user-specified correct hypothesis.
    
    It provides alternate words with associated probabilities for
    visualization, and tracks the user's corrected hypothesis.
    """
    def __init__(self, dag=None, lm=None, lscale=1./15):
        """
        Create a LatticeModel object.

        @param dag: Word lattice to initialize this object with.
        @type dag: lattice.Dag
        """
        self.lm = self.dag = None
        self.hyp = []
        if lm:
            self.set_lm(lm)
        if dag:
            self.set_dag(dag, lscale)

    def set_lm(self, lm=None):
        """
        Set the language model and update the best hypothesis and
        posterior probabilities with the new model.

        @param lm: Language model to use in computation
        @type lm: sphinxbase.NGramModel
        """
        self.lm = lm
        # Recompute the best path and posteriors
        if self.dag:
            self.set_dag(self.dag, lm, self.lscale)

    def set_dag(self, dag, lm=None, lscale=1./15):
        """
        Set the DAG and update the best hypothesis from its best path.

        @param dag: DAG to use.
        @type dag: lattice.Dag (or equivalent)
        @param lm: Language model to use in computation of best path
        @type lm: sphinxbase.NGramModel
        """
        self.lscale = lscale
        # Do bestpath search and get posterior probabilities
        link = dag.bestpath(self.lm, 1.0, lscale)
        dag.posterior(self.lm, lscale)
        # Backtrace to build hypothesis
        self.hyp = []
        # Check if we didn't reach </s> and thus must include the end node
        src, dest = link.nodes()
        if is_real_word(dest.baseword):
            self.hyp.append(LatticeWord(dest.baseword, dest.sf,
                                        dest.lef + 1, dest.prob))
        while link:
            if is_real_word(link.baseword):
                self.hyp.append(LatticeWord(link.baseword, link.sf,
                                            # these frame counts are
                                            # inclusive so add one to
                                            # the end.
                                            link.ef + 1, link.prob))
            link = link.pred()
        self.hyp.reverse()
        self.dag = dag

    def get_hyp(self):
        """
        Retrieve the best hypothesis from a LatticeModel

        @return: The top hypothesis, annotated with start and end
                 frames and posterior probabilities
        @rtype: list of LatticeWord
        """
        return self.hyp

    def set_hyp(self, hyp):
        """
        Set the best hypothesis

        @param hyp: The new top hypothesis
        @type hyp: list of LatticeWord
        """
        self.hyp = hyp

    def get_hyp_text(self):
        """
        Retrieve the text of the top hypothesis

        @return: The top hypothesis text
        @rtype: string
        """
        return " ".join([x.baseword for x in self.hyp])

class DisplayWord(object):
    """
    One word to be displayed in the lattice view.

    In addition to a lattice entry, these objects also keep track
    of their location and size within the lattice view.

    @ivar context: Pango context for drawing this word
    @type context: pango.Context
    @ivar layout: Pango layout for drawing this word
    @type layout: pango.Layout
    @ivar node: Lattice node corresponding to this word
    @type node: LatticeWord
    @ivar x: Horizontal origin (top-left of logical bounds)
    @type x: int
    @ivar y: Horizontal origin (top-left of logical bounds)
    @type y: int
    @ivar scale: Scaling factor applied when drawing
    @type scale: float
    """
    def __init__(self, context, desc, node, x, y, scale=1.0):
        """
        Initialize a DisplayWord.

        @param context: Pango context for drawing this word
        @type context: pango.Context
        @param desc: Pango font description for drawing this word
        @type desc: pango.FontDescription
        @param node: Lattice node corresponding to this word
        @type node: LatticeWord
        @param x: Horizontal origin (top-left of logical bounds)
        @type x: int
        @param y: Horizontal origin (top-left of logical bounds)
        @type y: int
        @param scale: Scaling factor applied when drawing
        @type scale:  float
        """
        self.context = context
        self.desc = desc
        self.node = node
        self.x = x
        self.y = y
        self.scale = scale

        # Now create a layout for this word
        self.layout = pango.Layout(self.context)
        self.layout.set_text(node.sym + " ")
        self.layout.set_font_description(desc)

        # Cache the extents
        bounds, extents = self.layout.get_pixel_extents()
        self.extents = list(extents)

    def contains(self, x, y):
        """
        Returns True if point (x,y) is inside this word's extents.

        @param x: Horizontal position of picking point
        @type x: int
        @param y: Vertical position of picking point
        @type y: int
        @return: True if point (x,y) is inside this word's extents
        @rtype: boolean
        """
        extents = self.get_extents()
        # If the bounds are impossibly narrow, add some extra space
        xfudge = yfudge = 0
        if extents[2] < 20:
            xfudge = (20 - extents[2]) / 2
        if extents[3] < 20:
            yfudge = (20 - extents[3]) / 2
        return (x >= extents[0] - xfudge
                and y >= extents[1] - yfudge
                and x <= extents[0] + extents[2] + xfudge * 2
                and y <= extents[1] + extents[3] + yfudge * 2)

    def set_scale(self, scale):
        """
        Set the scaling factor for this word.

        @param scale: Amount to scale this word in the display.
        @type scale: float
        """
        self.scale = scale

    def get_scale(self):
        """
        Return the scaling factor for this word.

        @return: Scaling factor for this word.
        @rtype: float
        """
        return self.scale

    def get_actual_size(self):
        """
        Return the actual font size for this word.

        @return: Font size for this word, in pango.SCALE units
        @rtype: float
        """
        return int(self.desc.get_size() * self.scale)

    def set_pos(self, x, y):
        """
        Set the position for this word.
        @param x: Horizontal origin (top-left of logical bounds)
        @type x: int
        @param y: Horizontal origin (top-left of logical bounds)
        @type y: int
        """
        self.x = x
        self.y = y

    def set_width(self, width):
        """
        Set the display width for this word.
        @param width: Display width (in parent coordinates)
        @type width: int
        """
        self.extents[2] = int(width / self.scale + 0.5)

    def get_extents(self):
        """
        Get the logical extents of this word in the LatticeView
        coordinate system.
        @return: the logical extentsof this word in the LatticeView
        coordinate system.
        @rtype: (int, int, int, int)
        """
        return (self.x + self.extents[0],
                self.y + self.extents[1],
                int(self.extents[2] * self.scale),
                int(self.extents[3] * self.scale))

    def draw(self, gc):
        """
        Draw this word in a given graphics context.

        @param gc: Cairo context (not to be confused with a Pango
        context) for drawing.
        @type gc: cairo.Context
        """
        gc.move_to(self.x, self.y)
        gc.scale(self.scale, self.scale)
        gc.show_layout(self.layout)

class DisplayCloud(LatticeCloud):
    """
    A "cloud" of words to be displayed in the lattice view.

    This object controls the presentation of and user interaction
    with a C{LatticeCloud}.  It lays out the words from a cloud
    according to their posterior probability and timing, and
    responds to resizing and click events.

    The user is able to select a set of correct words within a
    cloud.  These words are recorded by this object internally in
    the C{correct_words} list.

    @ivar context: Pango context for drawing this cloud
    @type context: pango.Context
    @ivar desc: Basic Pango font description for drawing this cloud
    @type desc: pango.FontDescription
    @ivar words: Set of word objects contained in this cloud.
    @type words: set(DisplayWord)
    @ivar hyp_words: Set of original hypothesis word objects in this cloud
    @type hyp_words: set(DisplayWord)
    @ivar corrected_words: Set of user-selected words
    @type corrected_words: set(DisplayWord)
    @ivar saved_word: Saved word from a previous click, for use in double-click handling
    @type saved_word: DisplayWord
    @ivar extents: Logical extents of this cloud
    @type extents: [int, int, int, int]
    @ivar min_extents: Minimum extents of this cloud
    @type min_extents: (int, int, int, int)
    @ivar max_extents: Maximum extents of this cloud
    @type max_extents: (int, int, int, int)
    @ivar edge_resistance: "Gravity zone" around minimum extents to which we snap.
    @type edge_resistance: int
    @ivar sign_x: Sign of a delta which "expands" the cloud horizontally
    @ivar sign_y: Sign of a delta which "expands" the cloud vertically
    @ivar scale: Scaling factor for drawing
    @type scale: float
    @ivar min_font_size: Minimum font size to use, in pango.SCALE units
    @type min_font_size: int
    """
    def __init__(self, parent, model, word):
        """
        Initialize a DisplayCloud.

        @param parent: Parent object for this DisplayCloud
        @type parent: LatticeView
        @param model: LatticeModel to get this cloud from.
        @type model: LatticeModel
        @param word: DisplayWord to use for the initial extents of this cloud.
        @type word: DisplayWord
        """
        LatticeCloud.__init__(self, model.dag, word.node.start, word.node.end)
        self.context = parent.get_pango_context()
        self.desc = parent.desc.copy_static()
        self.extents = list(word.get_extents())
        self.probscale = parent.probscale
        size = parent.get_size_request()
        # Determine minimum and maximum size
        self.min_extents = word.get_extents()
        self.max_extents = (parent.xpadding, parent.xpadding,
                            size[0] - parent.xpadding * 2,
                            size[1] - parent.xpadding * 2)
        # Map maximum beam width to available space
        self.beam_step = (self.max - self.min) / (self.max_extents[3] - self.min_extents[3])
        # Initial scaling factor is unity
        self.scale = 1.0
        # Add the current word as the initial one (note that it
        # might not be the MAP hypothesis)
        word.set_pos(0,0)
        self.words = set()
        self.words.add(word)
        self.hyp_words = set()
        self.hyp_words.add(word)
        self.corrected_words = set()
        self.saved_word = None
        self.edge_resistance = parent.edge_resistance
        self.min_font_size = parent.min_fontsize * pango.SCALE
        self.sign_x = self.sign_y = 0

    def contains(self, x, y):
        """
        Returns True if point (x,y) is inside this cloud's extents.

        @param x: Horizontal position of picking point
        @type x: int
        @param y: Vertical position of picking point
        @type y: int
        @return: True if point (x,y) is inside this cloud's extents
        @rtype: boolean
        """
        return (x >= self.extents[0]
                and y >= self.extents[1] \
                and x <= self.extents[0] + self.extents[2]
                and y <= self.extents[1] + self.extents[3])

    def y_expand(self, parent):
        """
        Expand the cloud to its maximum vertical size.

        @param parent: Parent widget
        @type parent: LatticeView
        """
        self.extents[1] = self.max_extents[1]
        self.extents[3] = self.max_extents[3]
        # Map vertical expansion to beam expansion
        self.set_beam((self.extents[3] - self.min_extents[3]) * self.beam_step)
        self.update_words()
        # Queue a redraw of our new extents (add a 5px border
        # to include the drawn border, this won't be necessary
        # when it is no longer used)
        parent.queue_draw_area(self.extents[0] - 5,
                               self.extents[1] - 5,
                               self.extents[2] + 10,
                               self.extents[3] + 10)

    def get_output_words(self):
        """
        Get the set of corrected words.  If no corrections have
        been made, this will return the set of original hypothesis
        words encompassed by this cloud.

        @return: The set of corrected (or original) words.  Note
                 that this is a reference to this set.  If you
                 wish to manipulated it, you must copy it!
        @rtype: set(DisplayWord)
        """
        if len(self.corrected_words) == 0:
            return self.hyp_words
        else:
            return self.corrected_words

    def collapse(self, parent):
        """
        Collapse the cloud to its minimum size, retaining any user
        corrections.

        @param parent: Parent widget
        @type parent: LatticeView
        """
        # Queue a redraw of previous extents
        parent.queue_draw_area(self.extents[0] - 5,
                               self.extents[1] - 5,
                               self.extents[2] + 10,
                               self.extents[3] + 10)
        # Collapse extents back to minimum
        self.extents[:] = self.min_extents[:]
        # Take output words to be new "hypothesized" and current words
        new_words = self.get_output_words().copy()
        self.words.clear()
        self.words.update(new_words)
        self.hyp_words.clear()
        self.hyp_words.update(new_words)
        # Remove set of corrected words
        self.corrected_words.clear()
        # Everything else is done by the parent, don't duplicate it

    def assimilate(self, parent, other):
        """
        Assimilate a neighbouring (we hope) cloud into this one.

        @param parent: Parent widget
        @type parent: LatticeView
        @param other: Cloud to be assimilated
        @type other: DisplayCloud
        """
        def merge_extents(a,b):
            """
            Merge two sets of extents.  This is actually just
            rectangle union and gtk can do that for us, but...
            """
            new_left = min(a[0], b[0])
            new_width = (max(a[0] + a[2], b[0] + b[2]) - new_left)
            new_top = min(a[1], b[1])
            new_height = (max(a[1] + a[3], b[1] + b[3]) - new_top)
            return (new_left, new_top, new_width, new_height)
        # Increase minimum extents to include other (maximum
        # extents should be the same for all clouds)
        self.min_extents = merge_extents(self.min_extents,
                                         other.min_extents)
        # Increase current extents to include other
        self.extents[:] = merge_extents(self.extents,
                                        other.extents)
        # Extend timepoints to include other
        self.set_time_extents(min(self.start, other.start),
                              max(self.end, other.end))
        # Assimilate any hypothesis and correction words from other
        self.hyp_words.update(other.hyp_words)
        self.corrected_words.update(other.corrected_words)
        # Now update all words
        self.update_words()
        # And redraw our new extents
        parent.queue_draw_area(self.extents[0] - 2,
                               self.extents[1] - 2,
                               self.extents[2] + 4,
                               self.extents[3] + 4)

    def find_word(self, x, y):
        """
        Find and return the display word in this cloud which contains point
        (x,y).
        @param x: Horizontal pixel position (in parent coordinates)
        @type x: int
        @param y: Vertical pixel position (in parent coordinates)
        @type y: int
        @return: Word in this cloud which contains point (x,y)
        @rtype: DisplayWord
        """
        # Translate (x,y) to word space coordinates
        x = (x - self.extents[0]) / self.scale
        y = (y - self.extents[1]) / self.scale
        for w in self.words:
            if w.contains(x, y):
                return w
        return None

    def double_click(self, parent, x, y):
        """
        React to a double click.

        @param parent: Parent widget
        @type parent: LatticeView
        @param x: Click point X
        @type x: int
        @param y: Click point Y
        @type y: int
        """
        # Undo removal of a word on double-click
        if self.saved_word:
            self.saved_word.node.set_prob(self.max)
            self.corrected_words.add(self.saved_word)
            self.saved_word = None

    def click(self, parent, x, y):
        """
        React to a discrete mouse click.

        @param parent: Parent widget
        @type parent: LatticeView
        @param x: Click point X
        @type x: int
        @param y: Click point Y
        @type y: int
        """
        # Remove any saved word for double clicking
        self.saved_word = None
        dw = self.find_word(x,y)
        if dw:
            # Toggle dw in corrected words
            if dw in self.corrected_words:
                # Save this so we can restore it if this turns out
                # to be a double-click
                self.saved_word = dw
                self.corrected_words.remove(dw)
                dw.node.reset_prob()
            else:
                # If the user thinks this word is correct, we'll give
                # it a posterior of 1.0.  Actually we should look at
                # this as a form of Bayesian update, but doing this
                # ensures that the darn thing will stick around!
                dw.node.set_prob(self.max)
                self.corrected_words.add(dw)
            # Translate word extents to parent coordinates
            dw_ext = [int(x * self.scale) for x in dw.get_extents()]
            dw_ext[0] += self.extents[0]
            dw_ext[1] += self.extents[1]
            # Queue a redraw inside those extents
            parent.queue_draw_area(*dw_ext)

    def drag_delta(self, parent, x, y, delta_x, delta_y):
        """
        React to drag motion of (delta_x, delta_y) to point (x,y).

        @param parent: Parent widget
        @type parent: LatticeView
        @param x: Destination point X
        @type x: int
        @param y: Destination point Y
        @type y: int
        @param delta_x: Horizontal distance travelled
        @type delta_x: int
        @param delta_y: Vertical distance travelled
        @type delta_y: int
        @return: The effective (x,y) delta after compensating for
                 drag direction.  This indicates the desired
                 change in size for this cloud.
        @rtype: (int, int)
        """
        # When starting the drag, determine which direction is
        # "out".  We will preserve this for the entire drag,
        # otherwise it becomes very difficult to fully "compress"
        # the cloud.
        if self.sign_y == 0:
            # If the cloud is collapsed, then clearly whichever
            # direction the user wanted to go is "expansion"
            if self.extents[1] == self.min_extents[1]:
                self.sign_y = delta_y
            # Otherwise, this depends on whether we're above or
            # below the centerline.
            else:
                center_y = self.extents[1] + self.extents[3] / 2
                self.sign_y = y - center_y
        if self.sign_x == 0:
            # Likewise for sign_x
            if self.extents[0] == self.min_extents[0]:
                self.sign_x = delta_x
            else:
                center_x = self.extents[0] + self.extents[2] / 2
                self.sign_x = x - center_x
        # Now modify the sign of delta in accordance
        if self.sign_y < 0: delta_y = -delta_y
        if self.sign_x < 0: delta_x = -delta_x

        # Implementation of edge resistance:
        # On an "outbound" drag (delta > 0), avoid redrawing until
        # the extents reach min_extents + edge_resistance
        if delta_y > 0:
            resistance_is_futile = (self.min_extents[1] -
                                    (self.extents[1] - int(delta_y))
                                    > self.edge_resistance)
        else:
            resistance_is_futile = True
        # On an "inbound" drag (delta < 0), snap immediately to
        # min_extents once we get within range.
        if delta_y < 0:
            you_will_be_assimilated = (self.min_extents[1] -
                                       (self.extents[1] - int(delta_y))
                                       < self.edge_resistance)
        else:
            you_will_be_assimilated = False
        # Queue a redraw of our current extents (add a 2px border
        # to include the outside of the drawn border)
        if resistance_is_futile:
            parent.queue_draw_area(self.extents[0] - 2,
                                   self.extents[1] - 2,
                                   self.extents[2] + 4,
                                   self.extents[3] + 4)
        # Vertical expansion
        self.extents[1] -= int(delta_y)
        self.extents[3] += int(delta_y * 2)
        # Ensure everything is symmetrical and inside bounds
        if self.extents[1] < self.max_extents[1]:
            self.extents[3] -= (self.max_extents[1] - self.extents[1]) * 2
            self.extents[1] = self.max_extents[1]
        # Don't shrink below min_extents
        self.extents[1] = min(self.extents[1], self.min_extents[1])
        self.extents[3] = max(self.extents[3], self.min_extents[3])
        # Snap to minimum size on an inbound drag
        if you_will_be_assimilated:
            self.extents[:] = self.min_extents[:]
        # Redraw unless there is edge resistance
        if resistance_is_futile:
            # Map vertical size to beam (don't use delta because we
            # clamped our size...)
            self.set_beam((self.extents[3] - self.min_extents[3]) * self.beam_step)
            # Update words
            self.update_words()
            # Queue a redraw of our new extents
            parent.queue_draw_area(self.extents[0] - 2,
                                   self.extents[1] - 2,
                                   self.extents[2] + 4,
                                   self.extents[3] + 4)
        return delta_x, delta_y

    def is_minimum(self):
        """
        Returns True if this cloud is at its minimum size.

        @return: True if this cloud is at its minimum size (duh)
        @rtype: boolean
        """
        return (self.extents[0] == self.min_extents[0]
                and self.extents[1] == self.min_extents[1])

    def end_drag(self, parent, x, y):
        """
        React to ending a drag at point (x,y)

        @param parent: Parent widget
        @type parent: LatticeView
        @param x: Destination point X
        @type x: int
        @param y: Destination point Y
        @type y: int
        """
        # Reset the drag direction
        self.sign_x = self.sign_y = 0

    def build_display_words(self, words):
        """
        Create a complete list of DisplayWords from a list of
        LatticeWords.  Words are scaled according to their
        probability, and the total width and height are returned.  No
        positioning is done.
        """
        # Compute total and maximum probability
        tprob = 0
        maxprob = 0
        for w in words:
            # Exponentiate to "flatten" probabilities
            # Also use inherent probability for scaling, so that
            # they don't jump in size.
            prob = math.exp(w.base_prob * self.probscale)
            if (prob > maxprob):
                maxprob = prob
            tprob += prob
        maxprob /= tprob
        # Now generate a list of display words (re-using existing
        # ones) and calculate their total height and width
        # Create a mapping of LatticeWord => DisplayWord
        dw_map = dict([(x.node, x) for x in self.words])
        # Make sure that any corrected words are present in this list!
        for dw in self.corrected_words:
            if dw.node not in dw_map:
                dw_map[dw.node] = dw
            if dw.node not in words:
                words.append(dw.node)
        display_words = []
        width = height = 0
        for w in words:
            wprob = math.exp(w.base_prob * self.probscale) / tprob
            # Look for an existing match
            if w in dw_map:
                dw = dw_map[w]
                dw.set_pos(0, height)
                # max = 1.0, others smaller
                dw.set_scale(1.0 + wprob - maxprob)
            else:
                dw = DisplayWord(self.context,
                                 self.desc, w,
                                 0, height,
                                 # max = 1.0, others smaller
                                 1.0 + wprob - maxprob)
            # Get the actual extents and track width/height
            dw_ext = dw.get_extents()
            if dw_ext[2] > width: width = dw_ext[2]
            # Increment height
            height += dw_ext[3]
            display_words.append(dw)
        return display_words, width, height

    def prune_display_words(self, display_words, width, height):
        """
        Prune the list of display words based on minimum effective font size.
        """
        # Find the appropriate scaling factor such that they will
        # all fit in the current bounding box.
        yscale = float(self.extents[3]) / height
        # Pop any words off the list that are just too small,
        # readjusting scale as we go.  Since they are sorted in
        # descending order this is a nice linear operation
        minsize = display_words[-1].get_actual_size() * yscale
        #print "minimum font size: %.3f" % (float(minsize) / pango.SCALE)
        # Keep track of corrected words that would otherwise get ditched
        extra_words = []
        while minsize < self.min_font_size \
                  and len(display_words) > 1: # make sure there is at least one!
            pinkie = display_words.pop()
            if pinkie in self.corrected_words:
                # FIXME: Also maintain minimum size for corrected words
                extra_words.append(pinkie)
            else:
                height -= pinkie.get_extents()[3]
                yscale = float(self.extents[3]) / height
            minsize = display_words[-1].get_actual_size() * yscale
        #print "updated minimum font size: %.3f" % (float(minsize) / pango.SCALE)
        # Put the corrected words back
        display_words.extend(extra_words)
        return width, height

    def position_display_words(self, display_words):
        """
        Position words vertically and horizontally
        """
        line = []          # List of current non-overlapping words
        line_height = 0    # Height of current line
        height = width = 0 # Overall height and width of cloud (unscaled)
        # Determine the ratio of unscaled pixels to frames
        cloud_width = (self.extents[2] / self.scale)
        time_step = cloud_width / (self.end - self.start)
        for dw in display_words:
            # First, place this word horizontally
            dw_left = max(0, int(time_step * (dw.node.start - self.start)))
            dw_right = min(cloud_width, int(time_step * (dw.node.end - self.start)))
            dw_ext = dw.get_extents()
            dw_width = dw_ext[2]
            # Look through extents on current line to see if anything overlaps
            for lw in line:
                ext = lw.get_extents()
                if (dw_left + dw_width > ext[0] 
                    and dw_left <= ext[0] + ext[2]):
                    #print "overlap: %s %s - %s %s" % (dw.node.sym, (dw_left, dw_width),
                    #                                  lw.node.sym, (ext[0], ext[2]))
                    height += line_height
                    line_height = 0
                    line = []
                    break
            dw.set_pos(dw_left, int(height))
            # Track width
            width = max(width, dw_left + dw_width)
            # Update line_height and line
            line_height = max(line_height, dw_ext[3])
            line.append(dw)
        # And add in the final line
        height += line_height
        return width, height

    def update_words(self):
        """
        Update the list of words to match extents.
        """
        # Obtain the list of words within the current beam
        words = list(self)
        if len(words) == 0:
            # Uh oh, no words.  Use the output hypothesis
            self.words.clear()
            self.words.update(self.get_output_words())
            return
        # Sort them in reverse by *inherent* probability - this
        # allows corrected words to retain their original place
        words.sort(lambda x,y: cmp(y.base_prob, x.base_prob))

        # Create a complete list of display words and track the
        # unscaled width and height
        display_words, width, height = self.build_display_words(words)
        #print "initial cloud: %d words %d x %d" % (len(display_words), width, height)

        # Prune list of display words to avoid tiny fonts
        width, height = self.prune_display_words(display_words, width, height)
        #print "updated cloud: %d words %d x %d" % (len(display_words), width, height)

        # "Reflect" the display words around the center of the
        # list, such that they become sorted in top-to-bottom
        # order with the highest probability in the middle.  Do
        # this by removing every other item and prepending these
        # in reverse order.
        botwords = display_words[1::2]
        display_words = display_words[0::2]
        display_words.reverse()
        display_words.extend(botwords)

        # Calculate a rough scaling factor
        xscale = float(self.extents[2]) / width
        yscale = float(self.extents[3]) / height
        self.scale = min(xscale, yscale)

        # Position words horizontally and vertically, collapsing
        # adjacent ones as necessary.
        width, height = self.position_display_words(display_words)

        # Update the scaling factors to reflect results of positioning
        xscale = float(self.extents[2]) / width
        yscale = float(self.extents[3]) / height
        self.scale = min(xscale, yscale)

        # Respace and center everything
        cwidth = width * self.scale
        cheight = height * self.scale
        xratio = self.extents[2] / cwidth
        yratio = self.extents[3] / cheight
        # Expand everything to fit the bounding box
        for dw in display_words:
            dw_ext = dw.get_extents()
            dw.set_pos(dw_ext[0] * xratio,
                       dw_ext[1] * yratio)
            width = max(width, dw_ext[0] * xratio + dw_ext[2])
            height = max(height, dw_ext[1] * yratio + dw_ext[3])
        # And finally center everything in it (could this be done above?)
        cwidth = width * self.scale
        cheight = height * self.scale
        xoff = (self.extents[2] - cwidth) / 2
        yoff = (self.extents[3] - cheight) / 2
        for dw in display_words:
            dw_ext = dw.get_extents()
            dw.set_pos(dw_ext[0] + xoff,
                       dw_ext[1] + yoff)

        # Update the set of active words for display
        self.words = set(display_words)

    def draw(self, gc):
        """
        Draw this cloud in a given graphics context.

        @param gc: Cairo context (not to be confused with a Pango
                   context) for drawing.
        @type gc: cairo.Context
        """
        # Stroke a red rectangle around the cloud
        gc.set_source_rgb(1.0,0,0)
        gc.rectangle(tuple(self.extents))
        gc.stroke()
        # Translate to set text
        gc.translate(self.extents[0], self.extents[1])
        # Scale to appropriate size
        gc.scale(self.scale, self.scale)
        # Draw all words
        for w in self.words:
            gc.save()
            # Draw corrected words in red, others in black
            if w in self.corrected_words:
                gc.set_source_rgb(1.0,0,0)
            else:
                gc.set_source_rgb(0,0,0)
            w.draw(gc)
            gc.restore()

class LatticeView(gtk.DrawingArea):
    """
    Handles the visual presentation of word lattices for multitouch
    error correction.  Since user input and display are tightly
    coupled, there is no separate controller object.

    @ivar model: Model object representing the word lattice
    @type model: LatticeModel

    @ivar words: Words in the display
    @type words: set(DisplayWord)

    @ivar clouds: Clouds in the display
    @type clouds: set(DisplayCloud)

    @ivar drag_state: State of dragging/expansion
    @type drag_state: int

    @ivar xpadding: Horizontal padding to add to the edges of the text
    @ivar ypadding: Vertical expansion area to add to the edges of the text
    @ivar fontsize: Basic font size for text
    @ivar probscale: Squashing factor to apply to probabilities
    """
    NO_DRAG   = 0 #: No dragging or expansion currently in progress
    PRE_DRAG  = 2 #: Dragging might start if the mouse moves
    IN_DRAG   = 3 #: Dragging is going on

    def __init__(self, model, *args, **kwargs):
        """
        Construct a LatticeView.

        @param model: model containing the word lattice and best
        hypothesis to be displayed.
        @type model: LatticeModel
        """
        # Initialize the base class
        gtk.DrawingArea.__init__(self)
        self.model = model
        # Set parameters with defaults
        self.xpadding = kwargs.get('xpadding', 25) 
        self.ypadding = kwargs.get('ypadding', 150)
        self.fontsize = kwargs.get('fontsize', 64)
        self.min_fontsize = kwargs.get('min_fontsize', 14)
        self.probscale = kwargs.get('probscale', 0.2)
        self.drag_thresh = kwargs.get('drag_thresh', 10)
        self.edge_resistance = kwargs.get('edge_resistance', 20)
        # Set up user interaction events
        self.add_events(gtk.gdk.BUTTON_PRESS_MASK
                        | gtk.gdk.BUTTON_RELEASE_MASK
                        | gtk.gdk.POINTER_MOTION_MASK)
        self.connect("button_press_event", self.button_press)
        self.connect("button_release_event", self.button_release)
        self.motion_notify_id = 0
        self.drag_state = self.NO_DRAG   #: Current state of dragging
        self.drag_word = None            #: Word currently being dragged
        self.drag_cloud = None           #: Cloud currently being dragged
        # Set up a handler for ConfigureEvents (resizing, etc)
        self.connect("configure_event", self.configure)
        # Set up our drawing function which responds to ExposeEvents (i.e. damage)
        self.connect("expose_event", self.expose)
        # Now refresh the set of words from the model.
        self.update_model()

    def update_model(self):
        # No clouds to start with
        self.clouds = set()
        # Create the set of individual words to draw
        self.words = set()
        # Set up the font used for drawing
        self.desc = pango.FontDescription()
        self.desc.set_size(int(self.fontsize * 1024))
        # Pango draws from the top-left corner
        x = self.xpadding
        y = self.ypadding
        height = 0
        for w in self.model.get_hyp():
            dw = DisplayWord(self.get_pango_context(),
                             self.desc.copy_static(),
                             w, x, y)
            self.words.add(dw)
            extents = dw.get_extents()
            # Advance the reference point by the logical width
            x += extents[2]
            height = extents[3]
        # If there were no words, then use a bogus one to get height
        if height == 0:
            w = LatticeWord("Bogus", 0.0, 0.0)
            dw = DisplayWord(self.get_pango_context(),
                             self.desc.copy_static(),
                             w, x, y)
            extents = dw.get_extents()
            height = extents[3]
        # Pad out the right side
        width = x + self.xpadding
        # And the bottom side (bottom edge is the same for all
        # words since it is calculated based on the ascent, descent,
        # and leading of the font rather than the actual glyphs)
        height = self.ypadding + height + self.ypadding
        # Set our requested size
        self.set_size_request(width, height)
        # Redraw everything
        self.queue_draw_area(*self.get_allocation())

    def find_word(self, x, y):
        """
        Find and return the display word (if any) which contains point
        (x,y).
        @param x: Horizontal pixel position inside this view.
        @type x: int
        @param y: Vertical pixel position inside this view.
        @type y: int
        @return: Word which contains point (x,y)
        @rtype: DisplayWord
        """
        for w in self.words:
            if w.contains(x, y):
                return w
        return None
            
    def find_cloud(self, x, y):
        """
        Find and return the display cloud (if any) which contains point
        (x,y).
        @param x: Horizontal pixel position inside this view.
        @type x: int
        @param y: Vertical pixel position inside this view.
        @type y: int
        @return: Cloud which contains point (x,y)
        @rtype: DisplayCloud
        """
        for c in self.clouds:
            if c.contains(x, y):
                return c
        return None

    def absorb_cloud(self, cloud):
        """
        Reclaim output words from a cloud and dispose of it.

        @param cloud: The cloud to get rid of
        @type cloud: DisplayCloud
        """
        cloud.collapse(self)
        # Now extract its output words and kill it
        # Sort words in time order
        new_words = list(cloud.get_output_words())
        new_words.sort(lambda x, y: cmp(x.node.start, y.node.start))
        # Reset their scaling factors (duh!)
        # And find the total width and height
        width = height = 0
        for dw in new_words:
            dw.set_scale(1.0)
            dw_ext = dw.get_extents()
            width += dw_ext[2]
            height = max(height, dw_ext[3])
        xscale = float(cloud.extents[2]) / width
        yscale = float(cloud.extents[3]) / height
        scale = min(xscale, yscale)
        # Figure out how much space needed to center them vertically
        yspace = (cloud.extents[3] - height * scale) / 2
        # Figure out how much extra space to put between words
        xspace = (cloud.extents[2] / scale - width) / len(new_words)
        # Now lay them out across the available space
        xpos = cloud.extents[0]
        ypos = int(cloud.extents[1] + yspace)
        # Calculate ratios for converting space to duration
        cloud_dur = cloud.end - cloud.start
        time_step = cloud_dur / float(cloud.extents[2])
        for i, dw in enumerate(new_words):
            dw.set_scale(scale)
            dw_ext = dw.get_extents()
            dw.set_pos(xpos, ypos)
            # Only adjust node widths if necessary (i.e. to fill space)
            # FIXME: this is still not entirely correct, as the
            # corrected words might overlap in time - not really clear
            # what to do in that case.
            if xspace > 0:
                dw_width = dw_ext[2] + xspace
                node_start = cloud.start + int((xpos - cloud.extents[0]) * time_step + 0.5)
                node_dur = int(dw_width * time_step + 0.5)
                dw.set_width(dw_ext[2] + xspace)
                #print "node_start was %d now %d" % (dw.node.start, node_start)
                #print "node_end was %d now %d" % (dw.node.end, node_start + node_dur)
                dw.node.start = node_start
                dw.node.end = node_start + node_dur
            self.words.add(dw)
            xpos = int(xpos + dw_ext[2] + xspace)
        self.clouds.remove(cloud)

    def extend_cloud(self, cloud, x, y):
        """
        Merge cloud with adjoining cloud or word at (x,y).

        @param cloud: The cloud to expand
        @type cloud: DisplayCloud
        @param x: Horizontal pixel position inside adjoining cloud/word
        @type x: int
        @param y: Vertical pixel position inside adjoining cloud/word
        @type y: int
        """
        # Figure out what cloud or word we just entered
        w = self.find_word(self.drag_x, cloud.extents[1] + cloud.extents[3] / 2)
        if w:
            # Create a new cloud for this word
            new_cloud = DisplayCloud(self, self.model, w)
            # Merge it into the current drag cloud
            cloud.assimilate(self, new_cloud)
            self.words.remove(w)
        else:
            # Look for a cloud
            c = self.find_cloud(self.drag_x, cloud.extents[1] + cloud.extents[3] / 2)
            if c:
                # Merge it and remove it from our list of clouds
                cloud.assimilate(self, c)
                self.clouds.remove(c)
            
    def button_press(self, widget, event):
        """
        Repond to button press events.

        @param widget: reference to widget where event occurred
        @type widget: gtk.Widget
        @param event: reference to the event
        @type event: gtk.gdk.Event
        """
        # Did we handle this event?
        handled = False
        # Handle doubleclicks
        if event.type == gtk.gdk._2BUTTON_PRESS:
            # Cancel any pending drags
            self.drag_state = self.NO_DRAG
            if self.motion_notify_id:
                self.disconnect(self.motion_notify_id)
                self.motion_notify_id = 0
            # If this happened in one of our words, it will be self.drag_word
            if self.drag_word:
                # Turn this word into a maximal cloud
                cloud = DisplayCloud(self, self.model, self.drag_word)
                # Expand it maximally
                cloud.y_expand(self)
                self.clouds.add(cloud)
                self.words.remove(self.drag_word)
                handled = True
            # If this happened in a cloud, it will be self.drag_cloud.
            elif self.drag_cloud:
                # Pass on the double click to the cloud - this might
                # undo a previous click.
                self.drag_cloud.double_click(self, event.x, event.y)
                # Collapse it, extract its output words, and kill it
                self.absorb_cloud(self.drag_cloud)
                handled = True
            # Clear any drag word/cloud
            self.drag_word = None
            self.drag_cloud = None
        # Handle button press
        elif event.type == gtk.gdk.BUTTON_PRESS:
            # We don't handle any dragging unless it's possible to expand words
            if self.model.dag == None:
                return False
            # Record click location to prepare for possible dragging
            self.drag_x = event.x
            self.drag_y = event.y
            self.drag_time = event.time
            # Start listening for motion notify events
            if self.motion_notify_id == 0:
                self.motion_notify_id = \
                                      self.connect("motion_notify_event",
                                                   self.motion_notify)
            # Check to see if this is in one of our words
            w = self.find_word(event.x, event.y)
            # If so...
            if w:
                # This might be a drag, but it might not.  Prepare for
                # that possibility by entering PRE_DRAG state
                self.drag_state = self.PRE_DRAG
                self.drag_word = w
                handled = True
            else:
                # Look for a cloud
                c = self.find_cloud(event.x, event.y)
                if c:
                    # Enter PRE_DRAG state with this cloud
                    self.drag_state = self.PRE_DRAG
                    self.drag_cloud = c
                    handled = True
        return handled

    def button_release(self, widget, event):
        """
        Repond to button release events.

        @param widget: reference to widget where event occurred
        @type widget: gtk.Widget
        @param event: reference to the event
        @type event: gtk.gdk.Event
        """
        # Did we handle this event?
        handled = False
        # Handle button release (probably won't get any other events
        # here actually)
        if event.type == gtk.gdk.BUTTON_RELEASE:
            # Handle the end of a drag
            if self.drag_state == self.IN_DRAG:
                # If we had a cloud, then terminate the drag on it
                if self.drag_cloud:
                    self.drag_cloud.end_drag(self, event.x, event.y)
                    # If it has reached minimum size, then eliminate it
                    if self.drag_cloud.is_minimum():
                        # Collapse it, extract its output words, and kill it
                        self.absorb_cloud(self.drag_cloud)
                self.drag_state = self.NO_DRAG
                self.drag_cloud = None
                if self.motion_notify_id:
                    self.disconnect(self.motion_notify_id)
                    self.motion_notify_id = 0
                handled = True
            # Otherwise cancel any drag in progress and handle a
            # single button press.
            elif self.drag_state == self.PRE_DRAG:
                self.drag_state = self.NO_DRAG
                if self.motion_notify_id:
                    self.disconnect(self.motion_notify_id)
                    self.motion_notify_id = 0
                # If this happened in a cloud (which would be
                # self.drag_cloud), then pass it on
                if self.drag_cloud:
                    self.drag_cloud.click(self, event.x, event.y)
                    self.drag_cloud = None
                handled = True
        return handled
    
    def motion_notify(self, widget, event):
        """
        Repond to motion notify events.

        @param widget: reference to widget where event occurred
        @type widget: gtk.Widget
        @param event: reference to the event
        @type event: gtk.gdk.Event
        """
        # Did we handle this event?
        handled = False
        if event.type == gtk.gdk.MOTION_NOTIFY:
            # Find the difference from the previous drag point
            delta_x = event.x - self.drag_x
            delta_y = event.y - self.drag_y
            delta_time = event.time - self.drag_time
            # If we were possibly going to drag, then confirm that we
            # are actually dragging by entering IN_DRAG state
            # immediately.  However, because of "jitter" on
            # touchscreens we should make sure that deltas are big
            # enough before we actually enter drag state.
            if self.drag_state == self.PRE_DRAG \
                    and (abs(delta_x) > self.drag_thresh or abs(delta_y) > self.drag_thresh):
                self.drag_state = self.IN_DRAG
                # Turn the drag word into a cloud, if needed
                if self.drag_word:
                    try:
                        self.drag_cloud = DisplayCloud(self, self.model, self.drag_word)
                        self.clouds.add(self.drag_cloud)
                    except:
                        self.drag_state = self.NO_DRAG
                        self.words.remove(self.drag_word)
                        self.drag_word = None
                        raise
                    # We no longer have a drag word
                    self.words.remove(self.drag_word)
                    self.drag_word = None
            # Now fall through to handle dragging
            if self.drag_state == self.IN_DRAG:
                # Avoid excessively frequent updates
                if abs(delta_x) < self.drag_thresh and abs(delta_y) < self.drag_thresh:
                    return True;
                # Update our drag point
                self.drag_x = event.x
                self.drag_y = event.y
                self.drag_time = event.time
                # Hand things off to the cloud for expansion (this
                # actually only does the Y direction)
                self.drag_cloud.drag_delta(self,
                                           self.drag_x, self.drag_y,
                                           delta_x, delta_y)
                # X direction works rather differently and needs to be
                # handled in the parent.  Basically what happens is
                # that on outbound drags, once drag_x crosses the
                # extent of this cloud plus some heuristically
                # determined threshold, this cloud will be merged with
                # the neighbouring one.
                if (delta_x > 0
                    and self.drag_cloud.sign_x > 0
                    and (self.drag_x
                         > (self.drag_cloud.extents[0]
                            + self.drag_cloud.extents[2] + 20))):
                    self.extend_cloud(self.drag_cloud, self.drag_x, self.drag_y)
                if (delta_x < 0
                    and self.drag_cloud.sign_x < 0
                    and (self.drag_x
                         < (self.drag_cloud.extents[0] - 20))):
                    self.extend_cloud(self.drag_cloud, self.drag_x, self.drag_y)
                handled = True
        return handled

    def configure(self, widget, event):
        """
        Respond to configure events.

        @param widget: reference to widget where event occurred
        @type widget: gtk.Widget
        @param event: reference to the event
        @type event: gtk.gdk.Event
        """
        return False

    def expose(self, widget, event):
        """
        Respond to expose events.

        @param widget: reference to widget where event occurred
        @type widget: gtk.Widget
        @param event: reference to the event
        @type event: gtk.gdk.Event
        """
        # Get a Cairo drawing context
        self.context = widget.window.cairo_create()
        # Add a rectangle to the current path (ahh.... this is like PostScript)
        self.context.rectangle(event.area.x, event.area.y,
                               event.area.width, event.area.height)
        # Clip based on the current path
        self.context.clip()
        # Now do some drawing
        self.draw()
        return False

    def draw(self):
        """
        Draw or re-draw the lattice presentation
        """
        # Get current size of this widget
        rect = self.get_allocation()
        # Draw a white background
        self.context.rectangle(rect)
        self.context.set_source_rgb(1,1,1)
        self.context.fill()
        # Draw words and clouds
        for dw in self.words:
            self.context.save()
            # Draw words in black
            self.context.set_source_rgb(0,0,0)
            dw.draw(self.context)
            self.context.restore()
        for dc in self.clouds:
            self.context.save()
            dc.draw(self.context)
            self.context.restore()

class KineticDragPort(gtk.Viewport):
    """
    Class implementing a viewport with horizontal kinetic scrolling.

    FIXME: For some reason this isn't double-buffered properly...
    """
    NO_DRAG = 0  #: No dragging is going on
    PRE_DRAG = 1 #: Button down, dragging might happen
    IN_DRAG = 2  #: Button down, dragging in progress

    def __init__(self, decay_factor=0.95, timeout=10):
        gtk.Viewport.__init__(self)
        self.decay_factor = decay_factor
        self.timeout = timeout
        self.add_events(gtk.gdk.BUTTON_PRESS_MASK
                        | gtk.gdk.BUTTON_RELEASE_MASK
                        | gtk.gdk.POINTER_MOTION_MASK)
        self.connect_after("button_press_event", self.button_press)
        self.connect_after("button_release_event", self.button_release)
        self.connect_after("size_allocate", self.handle_size_allocate)
        self.connect_after("add", self.handle_add)
        self.drag_state = self.NO_DRAG
        self.motion_notify_id = 0
        self.timeout_id = 0

    def handle_add(self, widget, child):
        # Record child size, so we can set our adjustments accordingly.
        child_size = child.size_request()
        # Connect to child's size_allocate signal to autoscroll
        child.connect_after("size_allocate", self.handle_child_resize)
        hadj = self.get_hadjustment()
        hadj.lower = 0
        hadj.upper = child_size[1]
        return False

    def handle_child_resize(self, child, allocation):
        hadj = self.get_hadjustment()
        if allocation.width > hadj.value + hadj.page_size:
            hadj.value = allocation.width - hadj.page_size

    def handle_size_allocate(self, widget, allocation):
        hadj = self.get_hadjustment()
        hadj.page_size = allocation.width
        return False

    def button_press(self, widget, event):
        self.drag_state = self.PRE_DRAG
        self.drag_x = event.x
        if self.motion_notify_id == 0:
            self.motion_notify_id = self.connect_after("motion_notify_event",
                                                       self.motion_notify)
        if self.timeout_id:
            gobject.source_remove(self.timeout_id)
            self.timeout_id = 0
        return True

    def button_release(self, widget, event):
        if self.drag_state == self.IN_DRAG:
            # Calculate average delta over this drag
            self.delta_x /= self.n_deltas
            # Set up a timeout function to do kinetic scrolling, with decaying deltas
            if self.timeout_id:
                gobject.source_remove(self.timeout_id)
            self.timeout_id = \
                            gobject.timeout_add(self.timeout,
                                                self.drag_decay)
        self.drag_state = self.NO_DRAG
        if self.motion_notify_id:
            self.disconnect(self.motion_notify_id)
            self.motion_notify_id = 0
        return True

    def drag_decay(self):
        self.delta_x *= self.decay_factor
        # Decayed too far
        if abs(self.delta_x) < 1:
            self.timeout_id = 0
            return False
        # Ran up against edge of child
        if self.scroll_hadj(self.delta_x):
            self.timeout_id = 0
            return False
        return True

    def motion_notify(self, widget, event):
        if self.drag_state == self.PRE_DRAG:
            self.drag_state = self.IN_DRAG
            self.delta_x = 0.
            self.n_deltas = 0
        if self.drag_state == self.IN_DRAG:
            delta_x = event.x - self.drag_x
            self.drag_x = event.x
            self.delta_x += delta_x
            self.n_deltas += 1
            self.scroll_hadj(delta_x)
        return True

    def scroll_hadj(self, delta_x):
        clipped = False
        hadj = self.get_hadjustment()
        value = hadj.value - delta_x
        if value < 0:
            value = 0
            clipped = True
        if value > hadj.upper - hadj.page_size:
            value = hadj.upper - hadj.page_size
            clipped = True
        hadj.value = value
        return clipped
