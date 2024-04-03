from django.shortcuts import render
from django.views import generic
import plotly.express as px
import pandas as pd
import os
from django.conf import settings
import plotly.graph_objects as go

# Create your views here.
def index(request):
    context = {

    }
    return render(request, "stock/index.html", context)