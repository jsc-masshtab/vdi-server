import { RemoveControllerComponent } from './../remove-controller/remove-controller.component';
import { FormForEditComponent } from './../../../common/forms-dinamic/change-form/form-edit.component';
import { MatDialog } from '@angular/material/dialog';
import { map } from 'rxjs/operators';
import { Subscription } from 'rxjs';
import { ControllersService } from './../all-controllers/controllers.service';
import { ActivatedRoute, Router, ParamMap } from '@angular/router';

import { Component, OnInit, OnDestroy } from '@angular/core';
import { IEditFormObj } from 'types';
import {FormControl} from '@angular/forms';
import { YesNoFormComponent } from 'src/app/dashboard/common/forms-dinamic/yes-no-form/yes-no-form.component';


@Component({
  selector: 'vdi-controller-details',
  templateUrl: './controller-details.component.html'
})


export class ControllerDetailsComponent implements OnInit, OnDestroy {
  private subController: Subscription;

  is_service = new FormControl(false);

  public host: boolean = false;
  public testing: boolean = false;
  public tested: boolean = false;
  public connected: boolean = false;

  public controller: any = {};

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
      title: 'Описание',
      property: 'description',
      type: 'string',
      formEdit: [{
        header: 'Изменение описания контроллера',
        tag: 'input',
        type: 'text',
        fieldName: 'description',
        fieldValue: this.controller['description']
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
      title: 'Токен',
      property: 'token',
      type: 'string',
      formEdit: [{
        header: 'Изменение токена интеграции контроллера',
        tag: 'input',
        type: 'text',
        fieldName: 'token',
        fieldValue: this.controller['token']
      }],
      edit: 'openEditForm',
    },
    {
      title: 'Версия',
      property: 'version',
      type: 'string'
    },
    {
      title: 'Статус',
      property: 'status',
      type: 'string'
    },
  ];

  public menuActive: string = 'info';
  private idController: string;

  filter: object

  constructor(
    private activatedRoute: ActivatedRoute,
    private router: Router,
    private controllerService: ControllersService,
    public  dialog: MatDialog
  ) {}

  ngOnInit() {
    this.activatedRoute.paramMap.subscribe((param: ParamMap) => {
      this.idController = param.get('id');
      this.getController();

      this.filter = {
        controller_id: this.idController
      }
    });
  }

  public getController(): void {
    if (this.subController) {
      this.subController.unsubscribe();
    }
    this.host = false;
    this.subController = this.controllerService.getController(this.idController).pipe(map((data: any) => data.data['controller']))
      .subscribe( (data) => {
        this.controller = data;
        this.host = true;
      },
      () => {
        this.host = true;
      });
  }


  public toggleService(e) {
    
    e.preventDefault();

    if (this.controller.status === 'SERVICE') {
      this.activateController();
    } else {
      this.serviceController();
    }
  }

  public serviceController() {
    this.dialog.open(YesNoFormComponent, {
      disableClose: true,
      width: '500px',
      data: {
        form: {
          header: 'Подтверждение действия',
          question: 'Перейти в сервисный режим?',
          button: 'Выполнить'
        },
        request: {
          service: this.controllerService,
          action: 'serviceController',
          body: {
            id: this.idController
          }
        }
      }
    }).afterClosed().subscribe(() => {
      this.getController();
    })
  }

  public activateController() {
    this.dialog.open(YesNoFormComponent, {
      disableClose: true,
      width: '500px',
      data: {
        form: {
          header: 'Подтверждение действия',
          question: 'Перейти в режим контроллера?',
          button: 'Выполнить'
        },
        request: {
          service: this.controllerService,
          action: 'activateController',
          body: {
            id: this.idController
          }
        }
      }
    }).afterClosed().subscribe(() => {
      this.getController();
    })
  }

  public test(): void {
    this.testing = true;
    this.controllerService.testController(
        this.idController
      )
      .subscribe((data) => {
        if (data) {
          setTimeout(() => {
            this.testing = false;
            this.tested = true;
            this.connected = data.data.testController.ok;
          }, 1000);

          setTimeout(() => {
            this.tested = false;
          }, 5000);
        } else {
          this.testing = false;
          this.tested = false;
        }
      });
  }

  public routeTo(route: string): void {
    this.menuActive = route
  }

  public edit(line: any) {
    this[line.edit](line);
  }

// @ts-ignore: Unreachable code error
  private openEditForm(activeObj: IEditFormObj): void  {
    activeObj['formEdit'][0]['fieldValue'] = this.controller[activeObj['property']];
    this.dialog.open(FormForEditComponent, {
      disableClose: true,
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
      disableClose: true,
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
