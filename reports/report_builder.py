# Python
import StringIO
from collections import OrderedDict, Counter

# Django
from django.utils.translation import ugettext_lazy as _
from django_countries import countries
from django.db.models import Count

# 3rd Party
import xlsxwriter

# Project
from forms.models import (
    InternetNewsSheet,
    TwitterSheet,
    NewspaperSheet,
    TelevisionSheet,
    RadioSheet,
    Person)
from forms.modelutils import TOPICS, GENDER, SPACE


sheet_models = OrderedDict([
    ('Internet News', InternetNewsSheet),
    ('Print', NewspaperSheet),
    ('Radio', RadioSheet),
    ('Television', TelevisionSheet),
    ('Twitter', TwitterSheet)]
)


MEDIA_TYPES = (
    (1, _('(1) Internet News')),
    (2, _('(2) Print')),
    (3, _('(3) Radio')),
    (4, _('(4) Television')),
    (5, _('(5) Twitter')),
)


def p(n, d):
    """ Helper to calculate the percentage of n / d,
    returning 0 if d == 0.
    """
    if d == 0:
        return 0.0
    return float(n) / d


class XLSXReportBuilder:
    def __init__(self, form):
        self.form = form
        self.countries = form.get_countries()
        self.gmmp_year = '2015'

    def build(self):
        """
        Generate an Excel spreadsheet and return it as a string.
        """
        output = StringIO.StringIO()
        workbook = xlsxwriter.Workbook(output)

        # setup formats
        self.P = workbook.add_format()
        self.P.set_num_format(9)  # percentage

        # Add generic sheets here.
        self.ws_2_media_by_country(workbook)
        self.ws_4_topics_by_region(workbook)
        self.ws_7_sex_by_media(workbook)
        self.ws_9_topic_by_source_sex(workbook)
        self.ws_10_space_per_topic(workbook)
        self.ws_13_topic_by_journalist_sex(workbook)

        workbook.close()
        output.seek(0)

        return output.read()

    def ws_2_media_by_country(self, wb):
        ws = wb.add_worksheet('2 - Medium per country')

        ws.write(0, 0, 'Participating Countries in each Region')
        ws.write(1, 0, 'Breakdown of all media by country')
        ws.write(3, 2, self.gmmp_year)

        ws.write(5, 0, 'Region name here')

        row, col = 6, 1

        # row headings
        for i, country in enumerate(self.countries):
            # Is this the best way to do this?
            ws.write(row + i, col, dict(countries)[country])

        col += 1

        counts = Counter()

        for media_type, model in sheet_models.iteritems():
            # row values
            rows = model.objects\
                    .values('country')\
                    .filter(country__in=self.countries)\
                    .annotate(n=Count('country'))

            counts.update({(media_type, r['country']): r['n'] for r in rows})

        row_totals = {}
        for country in self.countries:
            row_totals[country] = sum(counts.get((media_type, country), 0) for media_type, m in sheet_models.iteritems())

        for media_type, model in sheet_models.iteritems():
            # column title
            ws.write(row - 2, col, media_type)
            ws.write(row - 1, col, "N")
            ws.write(row - 1, col + 1, "%")

            # row values
            for i, country in enumerate(self.countries):
                c = counts.get((media_type, country), 0)
                ws.write(row + i, col, c)
                ws.write(row + i, col + 1, p(c, row_totals[country]), self.P)

            col += 2

    def ws_4_topics_by_region(self, wb):
        ws = wb.add_worksheet('4 - Topics by region')

        ws.write(0, 0, 'Topics in the news by region')
        ws.write(1, 0, 'Breakdown of major news topics by region by medium')
        ws.write(3, 2, self.gmmp_year)

        ws.write(5, 0, 'Region name here')

        row, col = 6, 1

        # row titles
        for i, topic in enumerate(TOPICS):
            id, topic = topic
            ws.write(row + i, col, unicode(topic))

        col += 1

        for media_type, model in sheet_models.iteritems():
            # column title
            ws.write(row - 2, col, media_type)
            ws.write(row - 1, col, "N")
            ws.write(row - 1, col + 1, "%")

            # row values
            rows = model.objects\
                    .values('topic')\
                    .filter(country__in=self.countries)\
                    .annotate(n=Count('topic'))
            counts = {r['topic']: r['n'] for r in rows}
            total = sum(counts.itervalues())

            for i, topic in enumerate(TOPICS):
                id, topic = topic
                ws.write(row + i, col, counts.get(id, 0))
                ws.write(row + i, col + 1, p(counts.get(id, 0), total), self.P)

            col += 2

    def ws_7_sex_by_media(self, wb):
        ws = wb.add_worksheet('7 - Sex by media')

        ws.write(0, 0, 'Women in the news (sources) by medium')
        ws.write(1, 0, 'Breakdown by sex of all mediums')
        ws.write(3, 2, self.gmmp_year)

        row, col = 6, 1

        # row titles
        for i, gender in enumerate(GENDER):
            id, gender = gender
            ws.write(row + i, col, unicode(gender))

        col += 1

        for media_type, model in sheet_models.iteritems():
            # column title
            ws.write(row - 2, col, media_type)
            ws.write(row - 1, col, "N")
            ws.write(row - 1, col + 1, "%")

            # row values
            sex = '%s__sex' % model.person_field_name()
            rows = model.objects\
                    .values(sex)\
                    .filter(country__in=self.countries)\
                    .annotate(n=Count('id'))
            counts = {r[sex]: r['n'] for r in rows if r[sex] is not None}
            total = sum(counts.itervalues())

            for i, topic in enumerate(GENDER):
                id, topic = topic
                ws.write(row + i, col, counts.get(id, 0))
                ws.write(row + i, col + 1, p(counts.get(id, 0), total), self.P)

            col += 2

    def ws_9_topic_by_source_sex(self, wb):
        ws = wb.add_worksheet('9 - Topic by source sex')

        ws.write(0, 0, 'Sex of news subjects in different story topics')
        ws.write(1, 0, 'Breakdown of topic by sex')
        ws.write(3, 2, self.gmmp_year)

        row, col = 6, 1

        # row titles
        for i, topic in enumerate(TOPICS):
            id, topic = topic
            ws.write(row + i, col, unicode(topic))

        col += 1
        counts = Counter()
        for media_type, model in sheet_models.iteritems():
            sex = '%s__sex' % model.person_field_name()
            rows = model.objects\
                    .values(sex, 'topic')\
                    .filter(country__in=self.countries)\
                    .annotate(n=Count('id'))
            counts.update({(r[sex], r['topic']): r['n'] for r in rows if r[sex] is not None})

        row_totals = {}
        for topic_id, t in TOPICS:
            row_totals[topic_id] = sum(counts.get((sex_id, topic_id), 0) for sex_id, s in GENDER)

        for i, gender in enumerate(GENDER):
            gender_id, gender = gender

            # column title
            ws.write(row - 2, col, unicode(gender))
            ws.write(row - 1, col, "N")
            ws.write(row - 1, col + 1, "%")

            # row values
            for i, topic in enumerate(TOPICS):
                topic_id, topic = topic
                c = counts.get((gender_id, topic_id), 0)
                ws.write(row + i, col, c)
                ws.write(row + i, col + 1, p(c, row_totals[topic_id]), self.P)

            col += 2

    def ws_10_space_per_topic(self, wb):
        ws = wb.add_worksheet('10 - Space per topic')

        ws.write(0, 0, 'Space allocated to major topics in Newspapers')
        ws.write(1, 0, 'Breakdown by major topic by space (q.4) in newspapers')
        ws.write(3, 2, self.gmmp_year)

        row, col = 6, 1

        # row titles
        for i, topic in enumerate(TOPICS):
            id, topic = topic
            ws.write(row + i, col, unicode(topic))

        col += 1

        for i, space in enumerate(SPACE):
            space_id, space_title = space
            # column title
            ws.write(row - 2, col, unicode(space_title))
            ws.write(row - 1, col, "N")
            ws.write(row - 1, col + 1, "%")

            # row values
            rows = NewspaperSheet.objects\
                    .values('topic')\
                    .filter(country__in=self.countries)\
                    .annotate(n=Count('topic'))
            counts = {r['topic']: r['n'] for r in rows if r['topic'] is not None}
            total = sum(counts.itervalues())

            for i, topic in enumerate(TOPICS):
                id, topic = topic
                ws.write(row + i, col, counts.get(id, 0))
                ws.write(row + i, col + 1, p(counts.get(id, 0), total), self.P)

            col += 2

    def ws_13_topic_by_journalist_sex(self, wb):
        ws = wb.add_worksheet('13 - Topic by reporter sex')

        ws.write(0, 0, 'Sex of reporter in different story topics')
        ws.write(1, 0, 'Breakdown of topic by reporter sex')
        ws.write(3, 2, self.gmmp_year)

        row, col = 6, 1

        # row titles
        for i, topic in enumerate(TOPICS):
            id, topic = topic
            ws.write(row + i, col, unicode(topic))

        col += 1

        counts = Counter()
        for media_type, model in sheet_models.iteritems():
            sex = '%s__sex' % model.journalist_field_name()
            rows = model.objects\
                    .values(sex, 'topic')\
                    .filter(country__in=self.countries)\
                    .annotate(n=Count('id'))
            counts.update({(r[sex], r['topic']): r['n'] for r in rows if r[sex] is not None})

        row_totals = {}
        for topic_id, t in TOPICS:
            row_totals[topic_id] = sum(counts.get((sex_id, topic_id), 0) for sex_id, s in GENDER)

        for i, gender in enumerate(GENDER):
            gender_id, gender = gender

            # column title
            ws.write(row - 2, col, unicode(gender))
            ws.write(row - 1, col, "N")
            ws.write(row - 1, col + 1, "%")

            # row values
            for i, topic in enumerate(TOPICS):
                topic_id, topic = topic
                c = counts.get((gender_id, topic_id), 0)
                ws.write(row + i, col, c)
                ws.write(row + i, col + 1, p(c, row_totals[topic_id]), self.P)

            col += 2
