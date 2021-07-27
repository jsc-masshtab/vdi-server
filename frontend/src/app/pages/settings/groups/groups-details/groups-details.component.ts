import { Component, OnInit, OnDestroy } from '@angular/core';
import { MatDialog } from '@angular/material/dialog';
import { ActivatedRoute, Router, ParamMap } from '@angular/router';
import { Subscription } from 'rxjs';

import { FormForEditComponent } from '../../../../shared/forms-dinamic/change-form/form-edit.component';
import { AddPermissionComponent } from '../add-permission/add-permission.component';
import { GroupsService} from '../groups.service';
import { RemoveGroupComponent } from '../remove-groups/remove-group.component';
import { RemovePermissionComponent } from '../remove-permission/remove-permission.component';
import { AddRoleComponent } from './add-role/add-role.component';
import { AddUserGroupComponent } from './add-users/add-user.component';
import { RemoveRoleComponent } from './remove-role/remove-role.component';
import { RemoveUserGroupComponent } from './remove-user/remove-user.component';


@Component({
  selector: 'groups-details',
  templateUrl: './groups-details.component.html',
  styleUrls: ['./groups-details.component.scss']
})
export class GroupsDetailsComponent implements OnInit, OnDestroy {

  private sub: Subscription;
  private id: string;
  public entity = {};
  public host: boolean = false;
  public menuActive: string = 'info';

  public collection: object[] = [
    {
      title: 'Название',
      property: 'verbose_name',
      class: 'name-start',
      icon: 'users-cog',
      type: 'string',
      formEdit: [{
        header: 'Изменение название группы',
        tag: 'input',
        type: 'text',
        fieldName: 'verbose_name',
        fieldValue: this.entity['verbose_name']
      }],
      edit: 'openEditForm',
    },
    {
      title: 'Описание',
      property: 'description',
      type: 'string',
      formEdit: [{
        header: 'Изменение описания группы',
        tag: 'input',
        type: 'text',
        fieldName: 'description',
        fieldValue: this.entity['description']
      }],
      edit: 'openEditForm',
    },
    {
      title: 'Пользователи',
      property: 'assigned_users',
      type: 'array-length'
    },
    {
      title: 'Время создания',
      property: 'date_created',
      type: 'time'
    },
    {
      title: 'Последнее редактирование',
      property: 'date_updated',
      type: 'time'
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

  public collection_users: object[] = [
    {
      title: 'Пользователи',
      type: 'string',
      property: 'username',
      class: 'name-start',
      icon: 'user'
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

  constructor(private service: GroupsService, private activatedRoute: ActivatedRoute, public dialog: MatDialog,
              private router: Router) {}

  ngOnInit() {
    this.activatedRoute.paramMap.subscribe((param: ParamMap) => {
      this.id = param.get('id');
      this.getGroup();
    });
  }

  public getGroup(): void {
    this.host = false;
    if (this.sub) {
      this.sub.unsubscribe();
    }

    this.sub = this.service.getGroup(this.id)
      .subscribe((data) => {
        this.host = true;
        this.entity = data.group;
      });
  }

  public edit(line: any) {
    this[line.edit](line);
  }

  // @ts-ignore: Unreachable code error
  private openEditForm(activeObj: IEditFormObj): void  {
    activeObj['formEdit'][0]['fieldValue'] = this.entity[activeObj['property']];
    this.dialog.open(FormForEditComponent, {
      disableClose: true,
      width: '500px',
      data: {
        post: {
          service: this.service,
          method: 'update',
          params: {
            id: this.id
          }
        },
        settings: {
          form: activeObj['formEdit'],
          buttonAction: 'Изменить',
          header: activeObj['formEdit'][0]['header']
        },
        update: {
          method: 'getGroup',
          params: [
            this.id
          ]
        }
      }
    });
  }

  public addRole() {
    this.dialog.open(AddRoleComponent, {
      disableClose: true,
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

  public addUser() {
    this.dialog.open(AddUserGroupComponent, {
      disableClose: true,
      width: '500px',
      data: {
        id: this.id,
        verbose_name: this.entity['verbose_name'],
        users: this.entity['possible_users']
      }
    });
  }

  public removeUser() {
    this.dialog.open(RemoveUserGroupComponent, {
      disableClose: true,
      width: '500px',
      data: {
        id: this.id,
        verbose_name: this.entity['verbose_name'],
        users: this.entity['assigned_users']
      }
    });
  }

  public removeGroup() {
    this.dialog.open(RemoveGroupComponent, {
      disableClose: true,
      width: '500px',
      data: {
        id: this.id,
        verbose_name: this.entity['verbose_name']
      }
    });
  }

  public addPermission() {
    this.dialog.open(AddPermissionComponent, {
      disableClose: true,
      width: '500px',
      data: {
        id: this.id,
        verbose_name: this.entity['verbose_name'],
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
        verbose_name: this.entity['verbose_name'],
        permissions: this.entity['assigned_permissions']
      }
    });
  }

  public routeTo(route: string): void {
    this.menuActive = route;
  }

  public close() {
    this.router.navigate(['pages/settings/groups']);
  }

  ngOnDestroy() {
    if (this.sub) {
      this.sub.unsubscribe();
    }
  }

}
