from fractions import Fraction
from writer import Jianpu99Writer
import re
import lxml.html


"""
byguitar add line no js
$('.muse-line').each(function(i,a){let no=parseInt(a.children[0].id.replace('muse-bars-', ''));$(a).append('<span class="line-no" style="position:absolute;margin-left:-25px;font-size:14px;padding:2px;border:1px solid #777;">'+no+'</span>');});
"""

class ByguitarWriter(Jianpu99Writer):

    STEP_TO_NUMBER = {
        'C': 'C',
        'D': 'D',
        'E': 'E',
        'F': 'F',
        'G': 'G',
        'A': 'A',
        'B': 'B'
    }

    def __init__(self, tempo):
        self.tempo_override = tempo

    def generateTimeSuffix(self, duration, divisions):
        note_length = Fraction(duration, divisions)
        return str(note_length)

    def generateBasicNote(self, note):
        #print( lxml.html.tostring(note._elem) )
        (duration, divisions) = self.getNoteDisplayedDuration(note)
        time_suffix = self.generateTimeSuffix(duration, divisions)
        if note.isRest():
            return "z" + time_suffix
        else:
            pitch = note.getPitch()
            (note_name, octave) = note.getPitch()

            keysig = note.getAttributes().getKeySignature()
            if keysig != 'C':
                offset = self.getTransposeOffsetToC(keysig)
                (note_name, octave) = self.getTransposedPitch(note_name, octave, offset)

            step = note_name[0:1] # C, D, E, F, G, A, B
            accidental = note_name[1:2] # sharp (#) and flat (b)
            if accidental == 'b':
                accidental = '_' 
            elif accidental == '#':
                accidental = '^'

            return accidental + self.stepToNumber(step) + self.generateOctaveMark(octave) + time_suffix

    def generateNote(self, note):
        result = self.generateBasicNote(note)
        if note.isTieStart():
            result = "(" + result
        if note.isTupletStart():
            result = "(3" + result
        if note.isTupletStop():
            #result = result + ")"
            pass
        if note.isTieStop():
            if '-' in result: # put ending tie before the first -
                idx = result.index('-')
                result = result[:idx] + ") " + result[idx:]
            else:
                result = result + ")"
        return result


    def sanitizeLyrics(self, l):
        return re.sub("[’‘]", "'", l)

    def generateLyricsMeasures(self, measureList):
        pieces = []
        for i, measure in enumerate(measureList):
            for note in measure:
                l = note.getLyric()
                if l:
                    pieces.append(self.sanitizeLyrics(l))
                elif not note.isRest() and not note.isChord():
                    pieces.append('*')

        pieces = list(filter(None, pieces))
        if pieces:
            return 'W: ' + ' '.join(pieces)
        return None

    def generateMeasure(self, measure):
        pieces = [self.generateNote(note) for note in measure if not note.isChord()]
        return ' '.join(pieces)

    def generateBody(self, reader, max_measures_per_line, target_part):
        parts = reader.getPartIdList()
        part_measures = dict()
        for part in parts:
            part_measures[part] = list(reader.iterMeasures(part))

        # split staff
        new_part_measures = {}
        for part_id, measures in part_measures.items():
            staffs = measures[0].getStaffs()
            if len(staffs) > 1:
                for staff_key in staffs.keys():
                    new_part_id = f'{part_id}-{staff_key}'
                    new_part_measures[new_part_id] = [m.cloneOnlyStaff((staff_key,)) for m in measures]
            else:
                new_part_measures[part_id] = measures

        part_measures = new_part_measures

        lines = []

        measure_count = max(len(measures) for measures in part_measures.values())
        for i in range(0, measure_count, max_measures_per_line):
            begin = i
            end = min(i + max_measures_per_line, measure_count)
            for part_index, part in enumerate(part_measures.keys()):
                if part_index != target_part:
                    continue
                line = self.generateMeasures(part_measures[part][begin:end])
                lines.append(line)

                lyrics_line = self.generateLyricsMeasures(part_measures[part][begin:end])
                if lyrics_line:
                    lines.append(lyrics_line)
                
            lines.append('') # empty line

        return '\n'.join(lines)
    
    def generate(self, reader, part_index):
        return self.generateBody(reader, 2, part_index)


    def generate_jcx(self, reader):
        def _getTempo():
            if self.tempo_override:
                return self.tempo_override
            return reader.getInitialTempo()

        parts_score = {}
        timesig = reader.getInitialTimeSignature()
        beats, beats_type = timesig.split('/')
        lines = [
            f'T: {reader.getWorkTitle()}',
            f'K: {reader.getInitialKeySignature()}',
            f'M: {beats}/{beats_type}',
            f'L: 1/{beats_type}',
            f'Q: 1/{beats_type}={_getTempo()}',
        ]

        parts = reader.getPartDetailsList()
        for i, part in enumerate(parts):
            lines.append(f'V:{part["id"]} name={part["name"]} style=jianpu ins=100 vol=100')
            parts_score[part['id']] = self.generateBody(reader, 2, i)

        lines.append('')
        for k, score in parts_score.items():
            lines.append(f'[V:{k}]')
            lines.append(score)

        return '\n'.join(lines)






