from celery.task import task
from django.conf import settings
from django.utils import simplejson as json
from .analyzers.loader import get_analyzers
from .ghclone import clone
from .models import Fix, Report
from .parsers import Parser


def parse(path):
    return Parser(path).parse()


def save_result(report, result):
    source = json.dumps(result.source)
    solution = json.dumps(result.solution)
    path = '/'.join(result.path.split('/')[1:]) # Remove archive dir name from result path
    Fix.objects.create(
        report=report, line=result.line, description=result.description,
        path=path, source=source, solution=solution
    )


def exception_handle(func):
    def decorator(report_pk, commit_hash=None):
        try:
            func(report_pk, commit_hash)
        except Exception, e:
            report = Report.objects.get(pk=report_pk)
            report.error = '%s: %s' % (e.__class__.__name__, unicode(e))
            report.save()
    decorator.__name__ = func.__name__
    return decorator


@task()
@exception_handle
def process_report(report_pk, commit_hash=None):
    report = Report.objects.get(pk=report_pk)
    report.stage = 'cloning'
    report.save()

    with clone(report.github_url, commit_hash) as path:
        report.stage = 'parsing'
        report.save()
        parsed_code = parse(path)

        report.stage = 'analyzing'
        report.save()
        for analyzer in get_analyzers():
            for result in analyzer(parsed_code, path).analyze():
                save_result(report, result)
        report.stage = 'done'
        report.save()
