import { Component, OnInit } from '@angular/core';
import { HttpResponse } from '@angular/common/http';
import { LicenseService } from './license.service';
import { ErrorsService } from 'src/app/errors/errors.service';
import { FooterService } from '../../common/components/single/footer/footer.service';

@Component({
  selector: 'vdi-license',
  templateUrl: './license.component.html',
  styleUrls: ['./license.component.scss']
})
export class LicenseComponent implements OnInit {

  license: any = {};

  collection: object[] = [
    {
      title: 'Название',
      property: 'verbose_name',
      type: 'string'
    },
    {
      title: 'Компания',
      property: 'company',
      type: 'string'
    },
    {
      title: 'Почта',
      property: 'email',
      type: 'string'
    },
    {
      title: 'Доступно тонких клиентов',
      property: 'thin_clients_limit',
      type: 'string'
    },
    {
      title: 'Активных тонких клиентов',
      property: 'thin_clients_count',
      type: 'string'
    },
    {
      title: 'Дата окончания лицензии',
      property: 'expiration_date',
      type: 'time'
    },
    {
      title: 'Дата окончания сервисной поддержки',
      property: 'support_expiration_date',
      type: 'time'
    }
  ];

  constructor(
    private service: LicenseService,
    private errorService: ErrorsService,
    private footer: FooterService) { }

  ngOnInit() {
    this.refresh();
  }

  refresh() {
    this.service.getLicence().subscribe((res) => {
      this.license = res.data;
    });
  }

  public upload(files): void {
    if (files.length === 0) {
      return;
    }

    const formData = new FormData();

    for (let file of files) {

      formData.append(file.name, file);
      formData.append('keyFile', file.name);

      this.service.upload('/api/license/', formData).subscribe((event: any) => {
        if (event instanceof HttpResponse) {
          this.refresh();

          if (event.body.errors) {
            this.errorService.setError(event.body.errors);
          }

          this.footer.reload();
        }
      });
    }
  }
}
