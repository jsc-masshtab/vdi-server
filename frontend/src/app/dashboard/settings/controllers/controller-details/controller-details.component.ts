import { RemoveControllerComponent } from './../remove-controller/remove-controller.component';
import { FormForEditComponent } from './../../../common/forms-dinamic/change-form/form-edit.component';
import { MatDialog } from '@angular/material';
import { map } from 'rxjs/operators';
import { Subscription } from 'rxjs';
import { ControllersService } from './../all-controllers/controllers.service';
import { ActivatedRoute, Router, ParamMap } from '@angular/router';

import { Component, OnInit, OnDestroy } from '@angular/core';
import { IEditFormObj } from 'types';


@Component({
  selector: 'vdi-controller-details',
  templateUrl: './controller-details.component.html'
})


export class ControllerDetailsComponent implements OnInit, OnDestroy {

  public host: boolean = false;

  public controller = {};
  public  menuActive: string = 'info';
  private subController: Subscription;
  private idController: string;

  public collection: any[] = [
    {
      title: 'Название',
      property: 'verbose_name',
      type: 'string',
      formEdit: [{
        header: 'Изменение имени контроллера',
        tag: 'input',
        type: 'text',
        fieldName: 'verbose_name',
        fieldValue: this.controller['verbose_name']
      }],
      edit: 'openEditForm',
    },
    {
      title: 'Адрес',
      property: 'address',
      type: 'string',
      formEdit: [{
        header: 'Изменение адреса контроллера',
        tag: 'input',
        type: 'text',
        fieldName: 'address',
        fieldValue: this.controller['address']
      }],
      edit: 'openEditForm',
    },
    {
      title: 'Версия',
      property: 'version',
      type: 'string'
    },
    {
      title: 'Логин для подключения',
      property: 'username',
      type: 'string',
      formEdit: [{
        header: 'Изменение логина контроллера',
        tag: 'input',
        type: 'text',
        fieldName: 'username',
        fieldValue: this.controller['username']
      }],
      edit: 'openEditForm',
    },
    {
      title: 'Пароль для подключения',
      property: 'password',
      type: 'string',
      formEdit: [{
        header: 'Изменение пароля контроллера',
        tag: 'input',
        type: 'text',
        fieldName: 'password',
        fieldValue: this.controller['password']
      }],
      edit: 'openEditForm',
    },
    {
      title: 'Использовать ldap подключение',
      property: 'ldap_connection',
      type: {
        typeDepend: 'boolean',
        propertyDepend: ['Да', 'Нет']
      },
      formEdit: [{
        header: 'Изменение ldap',
        tag: 'input',
        type: 'checkbox',
        fieldName: 'ldap_connection',
        fieldValue: this.controller['ldap_connection'],
        description: 'Использовать ldap подключение'
      }],
      edit: 'openEditForm',
    },
  ];

  constructor(private activatedRoute: ActivatedRoute,
              private router: Router,
              private controllerService: ControllersService,
              public  dialog: MatDialog
) {}

  ngOnInit() {
    this.activatedRoute.paramMap.subscribe((param: ParamMap) => {
      this.idController = param.get('id');
      this.getController();
    });
  }

  public getController(): void {
    if (this.subController) {
      this.subController.unsubscribe();
    }
    this.host = false;
    this.subController = this.controllerService.getController(this.idController).pipe(map((data) => data.data['controller']))
      .subscribe( (data) => {
        this.controller = data;
        this.host = true;
      },
      () => {
        this.host = true;
      });
  }

  public routeTo(route: string): void {
    if (route === 'info') {
      this.menuActive = 'info';
    }

    if (route === 'vms') {
      this.menuActive = 'vms';
    }

    if (route === 'users') {
      this.menuActive = 'users';
    }

    if (route === 'event-vm') {
      this.menuActive = 'event-vm';
    }
  }

  public edit(line: any) {
    this[line.edit](line);
  }

// @ts-ignore: Unreachable code error
  private openEditForm(activeObj: IEditFormObj): void  {
    activeObj['formEdit'][0]['fieldValue'] = this.controller[activeObj['property']];
    this.dialog.open(FormForEditComponent, {
      width: '500px',
      data: {
        post: {
          service: this.controllerService,
          method: 'updateController',
          params: {
            id: this.idController
          }
        },
        settings: {
          form: activeObj['formEdit'],
          buttonAction: 'Изменить',
          header: activeObj['formEdit'][0]['header']
        },
        update: {
          method: 'getController',
          params: [
            this.idController
          ]
        }
      }
    });
  }

  public removeController() {
    this.dialog.open(RemoveControllerComponent, {
      width: '500px',
      data: {
        id: this.idController,
        verbose_name: this.controller['verbose_name']
      }
    });
  }

  public close(): void  {
    this.router.navigateByUrl('pages/controllers');
  }

  ngOnDestroy() {
    if (this.subController) {
      this.subController.unsubscribe();
    }
  }
}
