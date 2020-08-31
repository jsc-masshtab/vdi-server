import { IParams } from '../../../../../../types';
import { WaitService } from '../../../common/components/single/wait/wait.service';
import { AddUserComponent } from '../add-user/add-user.component';
import { Component, OnInit, OnDestroy, ViewChild, ElementRef } from '@angular/core';
import { UsersService   } from '../users.service';
import { map } from 'rxjs/operators';
import { MatDialog } from '@angular/material';
import { Subscription } from 'rxjs';
import { Router } from '@angular/router';
import { DetailsMove } from '../../../common/classes/details-move';


@Component({
  selector: 'vdi-users',
  templateUrl: './users.component.html',
  styleUrls: ['./users.component.scss']
})

export class UsersComponent extends DetailsMove implements OnInit, OnDestroy {

  private getUsersSub: Subscription;

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
      title: 'Суперпользователь',
      property: 'is_superuser',
      type: {
        typeDepend: 'boolean',
        propertyDepend: ['Да', 'Нет']
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

  @ViewChild('view') view: ElementRef;

  ngOnInit() {
    this.getAllUsers();
  }

  public addUser() {
    this.dialog.open(AddUserComponent, {
 			disableClose: true, 
      width: '500px'
    });
  }

  public getAllUsers() {
    if (this.getUsersSub) {
      this.getUsersSub.unsubscribe();
    }

    this.waitService.setWait(true);

    this.getUsersSub = this.service.getAllUsers().valueChanges.pipe(map(data => data.data.users))
      .subscribe((data) => {
        this.users = data;
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
  }
}
