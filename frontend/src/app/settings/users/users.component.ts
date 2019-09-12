import { WaitService } from './../../common/components/wait/wait.service';
import { AddUserComponent } from './add-user/add-user.component';
import { Component, OnInit } from '@angular/core';
import { UsersService   } from './users.service';
import { map } from 'rxjs/operators';
import { MatDialog } from '@angular/material';


@Component({
  selector: 'vdi-users',
  templateUrl: './users.component.html',
  styleUrls: ['./users.component.scss']
})


export class UsersComponent implements OnInit {

  public users: [];
  public collection: object[] = [
    {
      title: 'Имя пользователя',
      property: 'username',
      class: 'name-start',
      icon: 'user'
    }
  ];

  constructor(private service: UsersService,public dialog: MatDialog,private waitService: WaitService){}

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
}
