import { HttpResponse } from '@angular/common/http';
import { Component, OnInit } from '@angular/core';

import { ErrorsService } from '@core/components/errors/errors.service';

import { LicenseService } from './license.service';

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
    private licenseService: LicenseService,
    private errorService: ErrorsService) { }

  ngOnInit() {
    this.refresh();
  }

  refresh() {
    this.licenseService.getLicence().subscribe((res) => {
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

      this.licenseService.uploadFile('/api/license/', formData).subscribe((event: any) => {
        if (event instanceof HttpResponse) {
          this.refresh();

          if (event.body.errors) {
            this.errorService.setError(event.body.errors);
          }

          this.licenseService.reload();
        }
      });
    }
  }
}
