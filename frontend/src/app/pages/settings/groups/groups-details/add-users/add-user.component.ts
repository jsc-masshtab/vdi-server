
import { Component, Inject, OnDestroy, OnInit } from '@angular/core';
import { FormControl } from '@angular/forms';
import { MatDialogRef } from '@angular/material/dialog';
import { MAT_DIALOG_DATA } from '@angular/material/dialog';
import { Subject } from 'rxjs';
import { debounceTime, takeUntil, map } from 'rxjs/operators';

import { WaitService } from '../../../../../core/components/wait/wait.service';
import { GroupsService } from '../../groups.service';

interface IData {
  id: string;
  verbose_name: string;
  users: string[]; // доступные для добавления в группу
  queryset: any;
}

@Component({
  selector: 'vdi-add-user',
  templateUrl: './add-user.component.html'
})
export class AddUserGroupComponent implements OnInit, OnDestroy {

  private destroy: Subject<any> = new Subject<any>();

  public isPending: boolean = false;
  public valid: boolean = true;

  public selected_users: string[] = [];

  users = new FormControl([]);
  search = new FormControl('');

  constructor(
    private service: GroupsService,
    private waitService: WaitService,
    private dialogRef: MatDialogRef<AddUserGroupComponent>,
    @Inject(MAT_DIALOG_DATA) public data: IData
  ) {}

  ngOnInit() {

    this.load();

    this.search.valueChanges.pipe(
      debounceTime(1000)
    ).subscribe((value) => {
      this.load(value)
    })
  }

  load(value = '') {

    const props = {};

    if (value) {
      props['username'] = value;
    }

    this.isPending = true;

    this.service.getPossibleUsersFromGroup(this.data.id, props).valueChanges.pipe(map((data: any) => data.data['group'])).subscribe((res: any) => {
      this.selected_users = [...res.possible_users] || []
      this.isPending = false;
    });
  }

  public send() {
    if (this.users.value.length) {
      this.waitService.setWait(true);
      this.service.addUsers(this.users.value, this.data.id).pipe(takeUntil(this.destroy)).subscribe((res) => {
        if (res) {
          this.service.getGroup(this.data.id, this.data.queryset).refetch()
          this.waitService.setWait(false);
          this.dialogRef.close();
        }
      });
    } else {
      this.valid = false;
    }
  }

  public select(value: []) {
    this.users = value['value'];
    this.valid = true;
  }

  public selectAllUsers() {
    this.users.setValue(this.selected_users.map((user: any) => user.id))
  }

  public deselectAllUsers() {
    this.users.setValue([])
  }

  ngOnDestroy() {
    this.destroy.next(null);
  }

}
