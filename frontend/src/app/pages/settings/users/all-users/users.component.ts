import { Component, OnInit, OnDestroy, ViewChild, ElementRef } from '@angular/core';
import { FormControl } from '@angular/forms';
import { MatDialog } from '@angular/material/dialog';
import { Router } from '@angular/router';
import { Subscription } from 'rxjs';
import { distinctUntilChanged, map } from 'rxjs/operators';

import { WaitService } from '@core/components/wait/wait.service';

import { DetailsMove } from '@shared/classes/details-move';
import { IParams } from '@shared/types';

import { AddUserComponent } from '../add-user/add-user.component';
import { UsersService   } from '../users.service';
import { FormForEditComponent } from '@app/shared/forms-dinamic/change-form/form-edit.component';

@Component({
  selector: 'vdi-users',
  templateUrl: './users.component.html',
  styleUrls: ['./users.component.scss']
})

export class UsersComponent extends DetailsMove implements OnInit, OnDestroy {

  private getUsersSub: Subscription;
  private getOptionsSub: Subscription;

  public limit = 100;
  public count = 0;
  public offset = 0;

  username = new FormControl('');
  is_active = new FormControl(true);
  is_superuser = new FormControl(false);

  queryset: any = {}

  public users: [];
  public collection: object[] = [
    {
      title: 'Имя пользователя',
      property: 'username',
      class: 'name-start',
      icon: 'user',
      type: 'string',
      sort: true
    },
    {
      title: 'Имя',
      property: 'first_name',
      type: 'string',
      sort: true
    },
    {
      title: 'Фамилия',
      property: 'last_name',
      type: 'string',
      sort: true
    },
    {
      title: 'E-mail',
      property: 'email',
      type: 'string',
      sort: true
    },
    {
      title: 'Администратор',
      property: 'is_superuser',
      type: {
        typeDepend: 'boolean',
        propertyDepend: ['Да', 'Нет']
      },
      sort: true
    },
    {
      title: 'Синхронизирован из AD',
      property: 'by_ad',
      type: {
        typeDepend: 'boolean',
        propertyDepend: ['Да', 'Нет']
      },
      sort: true
    },
    {
      title: 'Двухфакторная аутентификация',
      property: 'two_factor',
      type: {
        typeDepend: 'boolean',
        propertyDepend: ['Включена', 'Выключена']
      },
      sort: true
    },
    {
      title: 'Состояние',
      property: 'is_active',
      type: {
        typeDepend: 'boolean',
        propertyDepend: ['Активен', 'Не активен']
      },
      sort: true
    }
  ];

  constructor(private service: UsersService, public dialog: MatDialog, private waitService: WaitService,
              private router: Router) {
    super();
  }

  @ViewChild('view', { static: true }) view: ElementRef;

  ngOnInit() {
    this.refresh();

    this.username.valueChanges.subscribe(() => {
      this.getAllUsers();
    });

    this.is_active.valueChanges.subscribe(() => {
      this.getAllUsers();
    });

    this.is_superuser.valueChanges.subscribe(() => {
      this.getAllUsers();
    });

    this.service.portal$.subscribe((message) => {
      if (message === 'reload') {
        this.getAllUsers();
      }
    })
  }

  public addUser() {
    this.dialog.open(AddUserComponent, {disableClose: true,
      width: '500px',
      data: {
        queryset: this.queryset
      }
    });
  }

  public openSettings() {

    if (this.getOptionsSub) {
      this.getOptionsSub.unsubscribe();
    }

    this.getOptionsSub = this.service.getSettings().valueChanges.pipe(map((data: any) => data.data), distinctUntilChanged()).subscribe((res: any) => {
      this.dialog.open(FormForEditComponent, {
        disableClose: true,
        width: '500px',
        data: {
          post: {
            service: this.service,
            method: 'setSettings'
          },
          settings: {
            header: 'Политика авторизации пользователей',
            buttonAction: 'Изменить',
            form: [{
              tag: 'select',
              title: 'Уровень безопасности пароля',
              fieldName: 'PASSWORD_SECURITY_LEVEL',
              fieldValue: res.settings['PASSWORD_SECURITY_LEVEL'],
              data: ['LOW', 'MIDDLE', 'HIGH']
            }]
          }
        }
      });
    });
  }

  public getAllUsers() {
    if (this.getUsersSub) {
      this.getUsersSub.unsubscribe();
    }

    const queryset = {
      offset: this.offset,
      limit: this.limit,
      username: this.username.value,
      is_superuser: this.is_superuser.value,
      is_active: this.is_active.value
    };

    if (this.username.value === '') {
      delete queryset['username'];
    }

    if (this.is_active.value === false) {
      delete queryset['is_active'];
    }

    if (this.is_superuser.value === false) {
      delete queryset['is_superuser'];
    }

    this.waitService.setWait(true);

    this.queryset = queryset

    this.getUsersSub = this.service.getAllUsers(this.queryset).valueChanges.pipe(map((data: any) => data.data))
      .subscribe((data) => {
        this.users = data.users;
        this.count = data.count;
        this.waitService.setWait(false);
    });
  }

  public refresh(): void {
    this.service.paramsForGetUsers.spin = true;
    this.getAllUsers();
  }

  public sortList(param: IParams): void  {
    this.service.paramsForGetUsers.spin = param.spin;
    this.service.paramsForGetUsers.nameSort = param.nameSort;
    this.getAllUsers();
  }

  public routeTo(event): void {
    this.router.navigate([`pages/settings/users/${event.id}`]);
  }

  public toPage(message: any): void {
    this.offset = message.offset;
    this.getAllUsers();
  }

  public onResize(): void {
    super.onResize(this.view);
  }

  public componentActivate(): void {
    super.componentActivate(this.view);
  }

  public componentDeactivate(): void {
    super.componentDeactivate();
  }

  ngOnDestroy() {
    this.service.paramsForGetUsers.spin = true;
    this.service.paramsForGetUsers.nameSort = undefined;

    if (this.getUsersSub) {
      this.getUsersSub.unsubscribe();
    }

    if (this.getUsersSub) {
      this.getUsersSub.unsubscribe();
    }
  }
}
