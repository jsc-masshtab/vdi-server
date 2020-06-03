import { WaitService } from '../../../../common/components/single/wait/wait.service';
import { MatDialogRef } from '@angular/material';
import { Component, Inject, OnDestroy } from '@angular/core';
import { MAT_DIALOG_DATA } from '@angular/material';
import { Subject } from 'rxjs';
import { takeUntil, map } from 'rxjs/operators';

import { AuthenticationDirectoryService } from '../../auth-directory.service';

@Component({
  selector: 'vdi-add-group',
  templateUrl: './add-group.component.html'
})

export class AddGropComponent implements OnDestroy {

  public pending: boolean = false;
  public group: any = {};
  public members: [] = [];
  private destroy: Subject<any> = new Subject<any>();
  public valid: boolean = true;

  possible_ad_groups: [] = []
  group_members: [] = []

  constructor(private service: AuthenticationDirectoryService,
              private waitService: WaitService,
              private dialogRef: MatDialogRef<AddGropComponent>,
              @Inject(MAT_DIALOG_DATA) public data: any) { }

  ngOnInit() {
    this.load();
  }

  public load() {
    this.service.getAuthenticationDirectoryGroups(this.data.id)
      .valueChanges.pipe(map(data => data.data))
      .subscribe((data) => {
        this.possible_ad_groups = data.auth_dir.possible_ad_groups
      });
  }

  public getMembers(members) {
    this.service.getAuthenticationDirectoryGroupsMember(this.data.id, members)
      .valueChanges.pipe(map(data => data.data))
      .subscribe((data) => {
        this.group_members = data.group_members
      });
  }

  public send() {
    if (this.group) {

      const data = {
        group_members: this.members || null,
        auth_dir_id: this.data.id,
        group_ad_guid: this.group.ad_guid,
        group_verbose_name: this.group.verbose_name
      }

      this.waitService.setWait(true);
      this.service
        .syncAuthDirGroupUsers(data)
        .pipe(takeUntil(this.destroy)).subscribe((res) => {
          if (res) {
            this.service.getAuthenticationDirectory(this.data.id).refetch();
            this.waitService.setWait(false);
            this.dialogRef.close();
          }
        });
    } else {
      this.valid = false;
    }
  }

  public select(type, select) {

    if (type == 'groups') {

      this.group = select.value;
      this.valid = true;

      this.getMembers(select.value['ad_search_cn'])
    }

    if (type == 'members') {
      this.members = select.value;
    }
    
  }

  ngOnDestroy() {
    this.destroy.next(null);
  }

}
