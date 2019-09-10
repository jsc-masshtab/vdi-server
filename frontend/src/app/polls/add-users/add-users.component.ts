import { PoolsService } from './../pools.service';
import { UsersService } from './../../settings/users/users.service';
import { WaitService } from '../../common/components/wait/wait.service';
import { MatDialogRef } from '@angular/material';
import { Component,Inject } from '@angular/core';
import {MAT_DIALOG_DATA} from '@angular/material';
import { map } from 'rxjs/operators';


@Component({
  selector: 'vdi-add-users-pool',
  templateUrl: './add-users.component.html'
})

export class AddUsersPoolComponent  {

  public pendingUsers:boolean = false;
  public users: [] = [];
  private id_users: [] = [];

  constructor(private waitService: WaitService,
              private usersService: UsersService,
              private poolsService: PoolsService,
              private dialogRef: MatDialogRef<AddUsersPoolComponent>,
              @Inject(MAT_DIALOG_DATA) public data: any
             ) {}

  ngOnInit() {
    this.getUsers();
  }
 
  public send() {
    this.waitService.setWait(true);
    this.usersService.entitleUsersToPool(this.data.pool_id,this.id_users).subscribe(() => {
      this.dialogRef.close();
      this.poolsService.getPool(this.data.pool_id,this.data.pool_type).subscribe();
      this.waitService.setWait(false);
    });
  }

  private getUsers() {
    this.pendingUsers = true;
    this.usersService.getAllUsersNoEntitleToPool(this.data.pool_id).valueChanges.pipe(map(data => data.data.pool.users))
    .subscribe( (data) => {
      this.users =  data;
      this.pendingUsers = false;
    },
    (error) => {
      this.users = [];
      this.pendingUsers = false;
    });
  }

  public selectUser(value:[]) {
    this.id_users = value['value'];
  }

}
