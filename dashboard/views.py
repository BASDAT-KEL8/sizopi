from django.shortcuts import render, redirect

def dashboard_view(request):
    if 'email' not in request.session:
        return redirect('login')

    nama_lengkap = request.session.get('nama_lengkap', 'User')
    return render(request, 'dashboard/dashboard.html', {'nama_lengkap': nama_lengkap})










# XXX
