from django.shortcuts import render

def pipelineView(request):
    return render(request, 'help/pipeline.html')
