import { Component, OnInit, OnDestroy } from '@angular/core';
import { Subscription } from 'rxjs';
import { UsersService } from '../users.service';
import { ActivatedRoute, Router, ParamMap } from '@angular/router';
import { MatDialog } from '@angular/material';
import { FormForEditComponent } from 'src/app/dashboard/common/forms-dinamic/change-form/form-edit.component';
import { MutateUserComponent } from './mutate-user/mutate-user.component';

@Component({
  selector: 'user-details',
  templateUrl: './user-details.component.html',
  styleUrls: ['./user-details.component.scss']
})
export class UserDetailsComponent implements OnInit, OnDestroy {

  sub: Subscription;

  id: string;
  entity: any;

  public collection: object[] = [
    {
      title: 'Название',
      property: 'username',
      type: 'string',
      edit: 'openEditForm',
      form: {
        tag: 'input',
        type: 'text'
      }
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

  constructor(private service: UsersService, private activatedRoute: ActivatedRoute, public dialog: MatDialog,
              private router: Router) { }

  ngOnInit() {
    this.activatedRoute.paramMap.subscribe((param: ParamMap) => {
      this.id = param.get('id');
      this.getUser();
    });
  }

  public getUser(): void {
    if (this.sub) {
      this.sub.unsubscribe();
    }

    this.sub = this.service.getUser(this.id)
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

    this.dialog.open(FormForEditComponent, {
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
          method: 'getUser',
          params: [
            this.id
          ]
        }
      }
    });
  }

  public deactivateUser(): void {
    this.dialog.open(MutateUserComponent, {
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
          args: `$id: UUID!`,
          call: `id: $id`,
          props: {
            id: this.id,
          }
        }
      }
    });
  }

  public activateUser(): void {
    this.dialog.open(MutateUserComponent, {
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
          args: `$id: UUID!`,
          call: `id: $id`,
          props: {
            id: this.id,
          }
        }
      }
    });
  }

  public close() {
    this.router.navigate(['pages/settings/users']);
  }

  ngOnDestroy() {
    if (this.sub) {
      this.sub.unsubscribe();
    }
  }

}
