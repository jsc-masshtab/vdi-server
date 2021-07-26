import { Component, OnInit, OnDestroy } from '@angular/core';
import { Subscription } from 'rxjs';
import { UsersService } from '../users.service';
import { ActivatedRoute, Router, ParamMap } from '@angular/router';
import { MatDialog } from '@angular/material/dialog';
import { FormForEditComponent } from 'src/app/dashboard/common/forms-dinamic/change-form/form-edit.component';
import { MutateUserComponent } from './mutate-user/mutate-user.component';
import { AddGropComponent } from './add-group/add-group.component';
import { AddRoleComponent } from './add-role/add-role.component';
import { RemoveRoleComponent } from './remove-role/remove-role.component';

import { map } from 'rxjs/operators';
import { RemovePermissionComponent } from './remove-permission/remove-permission.component';
import { AddPermissionComponent } from './add-permission/add-permission.component';
import { GenerateQrcodeComponent } from './generate-qrcode/generate-qrcode.component';

@Component({
  selector: 'user-details',
  templateUrl: './user-details.component.html',
  styleUrls: ['./user-details.component.scss']
})
export class UserDetailsComponent implements OnInit, OnDestroy {

  sub: Subscription;

  id: string;
  entity: any;

  menuActive: string = 'info';

  public collection: object[] = [
    {
      title: 'Имя пользователя',
      property: 'username',
      type: 'string'
    },
    {
      title: 'Почтовый адрес',
      property: 'email',
      type: 'string',
      edit: 'openEditForm',
      form: {
        tag: 'input',
        type: 'text'
      }
    },
    {
      title: 'Имя',
      property: 'first_name',
      type: 'string',
      edit: 'openEditForm',
      form: {
        tag: 'input',
        type: 'text'
      }
    },
    {
      title: 'Фамилия',
      property: 'last_name',
      type: 'string',
      edit: 'openEditForm',
      form: {
        tag: 'input',
        type: 'text'
      }
    },
    {
      title: 'Администратор',
      property: 'is_superuser',
      type: {
        typeDepend: 'boolean',
        propertyDepend: ['Да', 'Нет']
      },
      edit: 'openEditForm',
      form: {
        tag: 'input',
        type: 'checkbox',
        description: 'Администратор',
        gqlType: 'Boolean'
      }
    },
    {
      title: 'Двухфакторная аутентификация',
      property: 'two_factor',
      type: {
        typeDepend: 'boolean',
        propertyDepend: ['Включена', 'Выключена']
      },
      edit: 'openGenerateQrcode'
    },
    {
      title: 'Дата создания',
      property: 'date_joined',
      type: 'time'
    },
    {
      title: 'Дата изменения',
      property: 'date_updated',
      type: 'time'
    },
    {
      title: 'Дата последней успешной авторизации',
      property: 'last_login',
      type: 'time'
    },
    {
      title: 'Статус активности',
      property: 'is_active',
      type: {
        typeDepend: 'boolean',
        propertyDepend: ['Активный', 'Не активный']
      }
    }
  ];

  public collection_roles: object[] = [
    {
      title: 'Роли',
      type: 'array-type',
      property: 'index-array',
      class: 'name-start',
      icon: 'users-cog'
    }
  ];

  public collection_groups: object[] = [
    {
      title: 'Название группы',
      type: 'string',
      property: 'verbose_name',
      class: 'name-start',
      icon: 'users-cog'
    }
  ];

  public collection_permissions: object[] = [
    {
      title: 'Разрешения',
      type: 'array-type-rename',
      property: 'index-array',
      class: 'name-start',
      icon: 'cog'
    }
  ];

  constructor(
    private service: UsersService,
    private activatedRoute: ActivatedRoute,
    public dialog: MatDialog,
    private router: Router
  ) {}

  ngOnInit() {
    this.activatedRoute.paramMap.subscribe((param: ParamMap) => {
      this.id = param.get('id');
      this.getUser();
    });
  }

  public routeTo(route: string): void {
    this.menuActive = route;
  }

  public getUser(): void {
    if (this.sub) {
      this.sub.unsubscribe();
    }

    this.sub = this.service.getUser(this.id)
      .valueChanges.pipe(map(data => data.data))
      .subscribe((data) => {
        this.entity = data.user;
      });
  }

  public edit(line: any) {
    this[line.edit](line);
  }

  public changeUserPassword(): void {
    const options = {
      header: 'Создание нового пароля',
      property: 'password',
      method: 'changeUserPassword',
      form: {
        tag: 'input',
        type: 'password',
        gqlType: 'String!'
      }
    };

    this.openEditForm(options);
  }

  public openEditForm(options): void {
    let gqlType: string = 'String';

    if (options.form.gqlType) {
      gqlType = options.form.gqlType;
    }

    this.dialog.open(FormForEditComponent, {disableClose: true,
      width: '500px',
      data: {
        post: {
          service: this.service,
          method: options.method || 'updateUser',
          params: {
            args: `$id: UUID!, $${options.property}: ${gqlType}`,
            call: `id: $id, ${options.property}: $${options.property}`,
            props: {
              id: this.id,
            }
          }
        },
        settings: {
          entity: 'user-details',
          header: options.header ? options.header : `Изменение свойства "${options.title}"`,
          buttonAction: 'Изменить',
          form: [{
            tag: options.form['tag'],
            type: options.form['type'],
            fieldName: options.property,
            fieldValue: this.entity[options.property],
            description: options.form['description'] || ''
          }]
        },
        update: {
          refetch: true,
          method: 'getUser',
          params: [
            this.id
          ]
        }
      }
    });
  }

  public deactivateUser(): void {
    this.dialog.open(MutateUserComponent, {disableClose: true,
      width: '500px',
      data: {
        id: this.id,
        item: this.entity,
        form: {
          header: 'Деактивация пользователя',
          question: 'Деактивировать пользователя',
          button: 'Деактивировать'
        },
        params: {
          method: 'deactivateUser',
          args: '$id: UUID!',
          call: 'id: $id',
          props: {
            id: this.id,
          }
        }
      }
    });
  }

  public activateUser(): void {
    this.dialog.open(MutateUserComponent, {disableClose: true,
      width: '500px',
      data: {
        id: this.id,
        item: this.entity,
        form: {
          header: 'Активация пользователя',
          question: 'Активировать пользователя',
          button: 'Активировать'
        },
        params: {
          method: 'activateUser',
          args: '$id: UUID!',
          call: 'id: $id',
          props: {
            id: this.id,
          }
        }
      }
    });
  }

  public 

  public close() {
    this.router.navigate(['pages/settings/users']);
  }

  public addGroup() {
    this.dialog.open(AddGropComponent, {disableClose: true,
      width: '500px',
      data: {
        id: this.id,
        verbose_name: this.entity['verbose_name'],
        groups: this.entity['possible_groups']
      }
    });
  }

  public removeGroup() {
    this.dialog.open(RemoveRoleComponent, {disableClose: true,
      width: '500px',
      data: {
        id: this.id,
        verbose_name: this.entity['verbose_name'],
        roles: this.entity['assigned_roles']
      }
    });
  }

  public addRole() {
    this.dialog.open(AddRoleComponent, {disableClose: true,
      width: '500px',
      data: {
        id: this.id,
        verbose_name: this.entity['verbose_name'],
        roles: this.entity['possible_roles']
      }
    });
  }

  public removeRole() {
    this.dialog.open(RemoveRoleComponent, {
      disableClose: true,
      width: '500px',
      data: {
        id: this.id,
        verbose_name: this.entity['verbose_name'],
        roles: this.entity['assigned_roles']
      }
    });
  }

  public addPermission() {
    this.dialog.open(AddPermissionComponent, {
      disableClose: true,
      width: '500px',
      data: {
        id: this.id,
        username: this.entity['username'],
        permissions: this.entity['possible_permissions']
      }
    });
  }

  public removePermission() {
    this.dialog.open(RemovePermissionComponent, {
      disableClose: true,
      width: '500px',
      data: {
        id: this.id,
        username: this.entity['username'],
        permissions: this.entity['assigned_permissions']
      }
    });
  }

  public openGenerateQrcode() {
    this.dialog.open(GenerateQrcodeComponent, {
      disableClose: true,
      width: '500px',
      data: {
        id: this.id,
        two_factor: this.entity['two_factor']
      }
    });
  }

  ngOnDestroy() {
    if (this.sub) {
      this.sub.unsubscribe();
    }
  }

}
