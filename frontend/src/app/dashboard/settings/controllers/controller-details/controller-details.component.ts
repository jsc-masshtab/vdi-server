import { map } from 'rxjs/operators';
import { Subscription } from 'rxjs';
import { ControllersService } from './../all-controllers/controllers.service';
import { ActivatedRoute, Router, ParamMap } from '@angular/router';

import { Component, OnInit, OnDestroy } from '@angular/core';


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
      type: 'string'
    },
    {
      title: 'Адрес',
      property: 'address',
      type: 'string'
    },
    {
      title: 'Версия',
      property: 'version',
      type: 'string'
    },
    {
      title: 'Логин для подключения',
      property: 'username',
      type: 'string'
    },
    {
      title: 'Пароль для подключения',
      property: 'username',
      type: 'string'
    },
    {
      title: 'Использовать ldap подключение',
      property: 'ldap_connection',
      type: 'string'
    }
  ];

  constructor(private activatedRoute: ActivatedRoute,
              private router: Router,
              private controllerService: ControllersService
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

  public removeController() {

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
