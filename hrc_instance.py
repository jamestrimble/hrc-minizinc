import sys
import time
import collections
from pprint import pprint as pp

class Instance(object):
    def __init__(self, lines, max_bp, presolve=True):
        self.max_bp = max_bp   # Maximum permitted number of blocking pairs

        self.read_lines(lines)
        if presolve: self.presolve()

    def read_lines(self, lines):
        self.nres = int(lines[0])
        self.nhosp = int(lines[1])
        self.ncoup = int(lines[2])
        self.nsingle = self.nres - 2 * self.ncoup
        self.first_single = 2 * self.ncoup
        self.couples = [(i*2, i*2+1) for i in range(self.ncoup)]
        self.singles = range(self.first_single, self.nres)
        self.npost = int(lines[3])
        lines = lines[9:]

        # Pref list for each resident
        self.rpref = [[int(x) for x in line.split()[1:]] for line in lines[:self.nres]]
        
        # Pref list for each hospital
        self.hpref = [[int(x) for x in line.split()[2:]] for line in lines[self.nres:self.nres+self.nhosp]]

        # Hospital capacities
        self.hosp_cap = [int(line.split()[1]) for line in lines[self.nres:self.nres+self.nhosp]]

    def presolve(self):
        """Reduce the size of the problem by removing some preferences that,
           if chosen, would result in too many blocking pairs.
        """

        q = collections.deque()  # Queue of residents to process
        in_q = [False] * self.nres
        for i in [r1 for r1, r2 in self.couples] + self.singles:
            q.append(i)
            in_q[i] = True

        while q:
            i = q.popleft()
            in_q[i] = False
            # num_bp counts the number of pairs that must be blocking pairs
            # if i doesn't get this or a better choice,
            # due to the low position of i on the hospital's preference list
            num_bp = 0
            if self.is_single(i):
                for j, hosp in enumerate(self.rpref[i][:-1]):
                    if self.hrank(hosp, i) < self.hosp_cap[hosp]:
                        num_bp += 1
                    if num_bp > self.max_bp:
                        #print "Cutting down pref list of res {} after pos {}".format(i, j)
                        self.remove_res_from_hosps(i, self.rpref[i][j+1:], q, in_q)
                        self.rpref[i] = self.rpref[i][:j+1]  # Trim resident's preferences
                        break
            else:
                for j, (hosp1, hosp2) in enumerate(zip(self.rpref[i][:-1], self.rpref[i+1][:-1])):
                    hosp1_cap = self.hosp_cap[hosp1]
                    if self.hrank(hosp1, i) < hosp1_cap:
                        if hosp1 == hosp2:
                            if self.hrank(hosp1, i+1) < hosp1_cap:
                                num_bp += 1
                        else:
                            hosp2_cap = self.hosp_cap[hosp2]
                            if self.hrank(hosp2, i+1) < self.hosp_cap[hosp2]:
                                num_bp += 1

                    if num_bp > self.max_bp:
                        # remove residents in this couple from preference lists of hospitals
                        # where they can no longer appear
                        for res in [i, i+1]:
                            # h_remove is the set of hospitals from whose pref lists we can remove resident res
                            h_remove = set(self.rpref[res])
                            for hosp in self.rpref[res][:j+1]: h_remove.discard(hosp)
                            self.remove_res_from_hosps(res, h_remove, q, in_q)
                            # Trim resident's preferences
                            self.rpref[res] = self.rpref[res][:j+1] 
                        break


        keep_going = True
        while keep_going:
            keep_going = self.presolve_truncate_hosp_prefs()

    def presolve_truncate_hosp_prefs(self):
        """For each hospital h, try to find and remove a suffix of h's pref list that can't be matched.

           For example, suppose we have a hospital with capacity 10, and that max_bp is 1.
           Further, suppose that of the first 14 residents on h's pref list, 11 are such
           that they are single and rank h first. Then, we can safely remove everything after
           the 14th element of h's pref list.

           Returns: whether any preferences were removed
        """
        truncated = False
        for h in range(self.nhosp):
            count = 0  # Number of residents who rank h first
            for j, r in enumerate(self.hpref[h][:-1]):
                if self.is_single(r):
                    if self.rrank(r, h)[0] == 0:
                        count += 1
                else:
                    partner = self.get_partner(r)
                    #print len(self.rpref[res]), len(self.rpref[partner])
                    partner_first_pref = self.rpref[partner][0]
                    if (self.rrank(r, h)[0] == 0 and partner_first_pref != h and
                            self.hrank(partner_first_pref, partner) < self.hosp_cap[partner_first_pref]):
                        count += 1
                if count == self.hosp_cap[h] + self.max_bp:
                    truncated = True
                    # residents_to_remove is the set of residents to be removed from the truncated hospital
                    # pref list. This will consist of partners of people in the truncated part of h's preference
                    # list such that h only appears in the partner's pref list at a position where the other
                    # partner also wishes to be assigned to h.
                    residents_to_remove = set()
                    for res in self.hpref[h][j+1:]:
                        if self.is_single(res):
                            self.rpref[res].remove(h)
                        else:
                            to_keep = [idx for idx, hosp in enumerate(self.rpref[res]) if hosp != h]
                            partner = self.get_partner(res)
                            hosps = set(self.rpref[partner]) # all hosps on partner's pref list
                            # all hosps that will remain on partner's pref list
                            hosps_to_keep = set(hosp for k, hosp in enumerate(self.rpref[partner]) if k in to_keep)
                            hosps_to_remove = hosps - hosps_to_keep
                            self.rpref[res] = [self.rpref[res][idx] for idx in to_keep]
                            self.rpref[partner] = [self.rpref[partner][idx] for idx in to_keep]
                            for hosp in hosps_to_remove:
                                if hosp == h:
                                    if self.hrank(h, partner) < j+1:
                                        residents_to_remove.add(partner)
                                else:
                                    self.hpref[hosp].remove(partner)
                    self.hpref[h] = self.hpref[h][:j+1]
                    for res in residents_to_remove:
                        self.hpref[h].remove(res)
#                    if X: print " ", self.hpref[h]
                    break
        return truncated

    def remove_res_from_hosps(self, res, hosps, q, in_q):
        """Remove resident res from hospitals in hosps as part of presolve.
           Residents who move into a hospital's top-k prefs, where k is the
           hospital's capacity, are added to the queue.
        """
        for hosp in hosps:
            self.hpref[hosp].remove(res)
            if len(self.hpref[hosp]) >= self.hosp_cap[hosp]:
                r = self.hpref[hosp][self.hosp_cap[hosp] - 1]
                if not in_q[r]:
                    if not self.is_single(r) and r % 2 == 1:
                        r -= 1  # Always add the first member of a couple
                    q.append(r)
                    in_q[r] = True


    def padded_2d_array(self, arr, row_len, add_to_each):
        arr_ = [row + [-1]*(row_len - len(row)) for row in arr]
        return "\n     ".join("|{}".format(",".join(str(x+add_to_each) for x in row)) for row in arr_)

    def array(self, arr):
        return ",".join(str(x) for x in arr)

    def hrank_or_minus_1(self, h, r):
        "Return hrank(h, r) or -1 if h doesn't rank r"
        try:
            return self.hrank(h, r)
        except ValueError:
            return -1

    def write_dzn(self):
        print "num_bp = {};".format(self.max_bp)
        print "nres = {};".format(self.nres)
        print "ncoup = {};".format(self.ncoup)
        print "nhosp = {};".format(self.nhosp)
        max_res_pref_len = max(len(self.rpref[i]) for i in range(self.nres))
        max_hosp_pref_len = max(len(self.hpref[i]) for i in range(self.nhosp))
        print "max_rpref_len = {};".format(max_res_pref_len)
        print "max_hpref_len = {};".format(max_hosp_pref_len)
        print "rpref = [{}|];".format(self.padded_2d_array(self.rpref, max_res_pref_len+1, 1))
        print "rpref_len = [{}];".format(self.array(len(prefs) for prefs in self.rpref))
        print "hpref = [{}|];".format(self.padded_2d_array(self.hpref, max_hosp_pref_len, 1))
        print "hpref_len = [{}];".format(self.array(len(prefs) for prefs in self.hpref))
        print "hrank = [{}|];".format(self.padded_2d_array([[self.hrank_or_minus_1(h, r) for r in range(self.nres)] for h in range(self.nhosp)], self.nres, 1))
        print "hosp_cap = [{}];".format(self.array(self.hosp_cap))

    def is_single(self, res):
        return res >= self.first_single

    def get_partner(self, res):
        "Returns the ID of the partner of res, who is assumed to be in a couple"
        return res + 1 if res % 2 == 0 else res - 1

    def rrank(self, r, h):
        """What ranks does resident r give hospital h (as an array)?
           Note that a resident in a couple may rank a hospital more than once
        """
        return [i for i, hosp in enumerate(self.rpref[r]) if hosp == h]
            
    def hrank(self, h, r):
        "What rank does hospital h give resident r?"
        return self.hpref[h].index(r)

