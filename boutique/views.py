import datetime
from django.template.loader import get_template
from django.http import HttpResponse
from .utils import pagination, get_invoice
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db import transaction
from django.shortcuts import render
from django.views import View
from .models import *
from django.contrib import messages
import pdfkit


class HomeView(View):
    """ Main view """

    templates_name = 'index.html'

    invoices = Invoice.objects.select_related(
        'customer', 'save_by').all().order_by('-invoice_date_time')

    context = {
        'invoices': invoices
    }

    def get(self, request, *args, **kwargs):

        items = pagination(request, self.invoices)

        self.context['invoices'] = items

        return render(request, self.templates_name, self.context)

    def post(self, request, *args, **kwagrs):

        # modify an invoice

        if request.POST.get('id_modified'):

            paid = request.POST.get('modified')

            try:

                obj = Invoice.objects.get(id=request.POST.get('id_modified'))

                if paid == 'True':

                    obj.paid = True

                else:

                    obj.paid = False

                obj.save()

                messages.success(request, ("Change made successfully."))

            except Exception as e:

                messages.error(
                    request, f"Sorry, the following error has occured {e}.")

                # deleting an invoice

        if request.POST.get('id_supprimer'):

            try:

                obj = Invoice.objects.get(pk=request.POST.get('id_supprimer'))

                obj.delete()

                messages.success(request, ("The deletion was successful."))

            except Exception as e:

                messages.error(
                    request, f"Sorry, the following error has occured {e}.")

        items = pagination(request, self.invoices)

        self.context['invoices'] = items

        return render(request, self.templates_name, self.context)


class AddCustomerView(View):
    """ add new customer """
    template_name = 'add_customer.html'

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name)

    def post(self, request, *args, **kwargs):

        data = {
            'name': request.POST.get('name'),
            'email': request.POST.get('email'),
            'phone': request.POST.get('phone'),
            'address': request.POST.get('address'),
            'sex': request.POST.get('sex'),
            'age': request.POST.get('age'),
            'city': request.POST.get('city'),
            'zip_code': request.POST.get('zip'),
            'save_by': request.user

        }

        try:
            created = Customer.objects.create(**data)
            if created:
                messages.success(request, "Customer registered successfully.")
            else:
                messages.error(
                    request, "Sorry, please try again the sent data is corrupt.")

        except Exception as e:
            messages.error(
                request, f"Sorry our system is detecting the following issues {e}.")

        return render(request, self.template_name)


class AddInvoiceView(View):
    """ add a new invoice view """

    template_name = 'add_invoice.html'

    customers = Customer.objects.select_related('save_by').all()

    context = {
        'customers': customers
    }

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, self.context)

    @transaction.atomic()
    def post(self, request, *args, **kwargs):

        items = []

        try:

            customer = request.POST.get('customer')

            type = request.POST.get('invoice_type')

            articles = request.POST.getlist('article')

            qties = request.POST.getlist('qty')

            units = request.POST.getlist('unit')

            total_a = request.POST.getlist('total-a')

            total = request.POST.get('total')

            comment = request.POST.get('commment')

            invoice_object = {
                'customer_id': customer,
                'save_by': request.user,
                'total': total,
                'invoice_type': type,
                'comments': comment
            }

            invoice = Invoice.objects.create(**invoice_object)

            for index, article in enumerate(articles):

                data = Article(
                    invoice_id=invoice.id,
                    name=article,
                    quantity=qties[index],
                    unit_price=units[index],
                    total=total_a[index],
                )

                items.append(data)

            created = Article.objects.bulk_create(items)

            if created:
                messages.success(request, "Data saved successfully.")
            else:
                messages.error(
                    request, "Sorry, please try again the sent data is corrupt.")

        except Exception as e:
            messages.error(
                request, f"Sorry the following error has occured {e}.")

        return render(request, self.template_name, self.context)


class InvoiceVisualizationView(View):
    """ This view helps to visualize the invoice """
    template_name = 'invoice.html'

    def get(self, request, *args, **kwargs):
        pk = kwargs.get('pk')
        context = get_invoice(pk)
        return render(request, self.template_name, context)

    def get(request, *args, **kwargs):

        pk = kwargs.get('pk')

        context = get_invoice(pk)

        context['date'] = datetime.datetime.today()

    # get html file
        template = get_template('invoice-pdf.html')

    # render html with context variables

        html = template.render(context)

    # options of pdf format

        options = {
            'page-size': 'Letter',
            'encoding': 'UTF-8',
            "enable-local-file-access": ""
        }

    # generate pdf

        pdf = pdfkit.from_string(html, False, options)

        response = HttpResponse(pdf, content_type='application/pdf')

        response['Content-Disposition'] = "attachement"
        response['Content-Disposition'] = "attachment; filename=invoice.pdf"

        return response
