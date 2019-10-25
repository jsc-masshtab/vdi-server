import { IParams } from './../../../../../types/index.d';
import { WaitService } from '../../../common/components/single/wait/wait.service';
import { AddUserComponent } from '../add-user/add-user.component';
import { Component, OnInit, OnDestroy } from '@angular/core';
import { UsersService   } from './users.service';
import { map } from 'rxjs/operators';
import { MatDialog } from '@angular/material';


@Component({
  selector: 'vdi-users',
  templateUrl: './users.component.html',
  styleUrls: ['./users.component.scss']
})


export class UsersComponent implements OnInit, OnDestroy {

  public users: [];
  public collection: object[] = [
    {
      title: 'Имя пользователя',
      property: 'username',
      class: 'name-start',
      icon: 'user',
      type: 'string',
      reverse_sort: true
    },
    /*{
      title: 'Дата создания',
      property: 'date_joined',
      type: 'time',
      reverse_sort: true
    }*/
  ];

  constructor(private service: UsersService, public dialog: MatDialog, private waitService: WaitService) {}

  ngOnInit() {
    this.getAllUsers();
  }

  public addUser() {
    this.dialog.open(AddUserComponent, {
      width: '500px'
    });
  }

  public getAllUsers() {
    this.waitService.setWait(true);
    this.service.getAllUsers().valueChanges.pipe(map(data => data.data.users))
      .subscribe((data) => {
        this.users = data;
        this.waitService.setWait(false);
    });
  }

  public sortList(param: IParams): void  {
    this.service.paramsForGetUsers.spin = param.spin;
    this.service.paramsForGetUsers.nameSort = param.nameSort;
    this.service.paramsForGetUsers.reverse = param.reverse;
    this.getAllUsers();
  }

  ngOnDestroy() {
    this.service.paramsForGetUsers.spin = true;
    this.service.paramsForGetUsers.nameSort = undefined;
    this.service.paramsForGetUsers.reverse = undefined;
  }
}
