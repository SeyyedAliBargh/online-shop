from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy
from .models import Profile
# Create your views here.


def edit_profile(request, pk):
    """
    Handle profile editing for a specific user.
    Updates first name, last name, birthdate, and profile image.
    After successful update, redirects the user to their profile page.
    :param request:
    :param pk:
    :return:
    """
    profile = get_object_or_404(Profile, pk=pk)
    if request.method == "POST":
        profile.first_name = request.POST.get("first_name")
        profile.last_name = request.POST.get("last_name")
        profile.birth_date = request.POST.get("birth_date")
        if request.FILES.get("image"):
            profile.image = request.FILES["image"]
        profile.save()
        # TODO: create a ProfileDetailView and redirect to the user's profile page after saving
        return redirect('shop:index')

    return render(request, 'account/edit_profile.html', {"profile": profile})


