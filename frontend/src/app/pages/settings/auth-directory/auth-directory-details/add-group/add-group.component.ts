import { Component, Inject, OnDestroy, OnInit } from '@angular/core';
import { FormControl } from '@angular/forms';
import { MatDialogRef } from '@angular/material/dialog';
import { MAT_DIALOG_DATA } from '@angular/material/dialog';

import { Subject } from 'rxjs';
import { takeUntil, map, debounceTime } from 'rxjs/operators';

import { WaitService } from '../../../../../core/components/wait/wait.service';
import { AuthenticationDirectoryService } from '../../auth-directory.service';

@Component({
  selector: 'vdi-add-group',
  templateUrl: './add-group.component.html'
})

export class AddGropComponent implements OnInit, OnDestroy {

  public pending: boolean = false;
  public group: any = {};
  private destroy: Subject<any> = new Subject<any>();
  public valid: boolean = true;

  group_name = new FormControl('');

  possible_ad_groups: [] = [];

  constructor(private service: AuthenticationDirectoryService,
              private waitService: WaitService,
              private dialogRef: MatDialogRef<AddGropComponent>,
              @Inject(MAT_DIALOG_DATA) public data: any) { }

  ngOnInit() {
    this.searching();
    this.load();
  }

  public searching() {
    this.group_name.valueChanges.pipe(
      debounceTime(1000)
    ).subscribe(() => {
      this.load()
    })
  }

  public load() {
    this.service.getAuthenticationDirectoryGroups(this.data.id, this.group_name.value)
      .valueChanges.pipe(map(data => data.data))
      .subscribe((data) => {
        this.possible_ad_groups = data.auth_dir.possible_ad_groups
      });
  }

  public send() {
    if (this.group) {

      const data = {
        group_ad_cn: this.group.ad_search_cn,
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
    if (type === 'groups') {
      this.group = select.value;
      this.valid = true;
    }
  }

  ngOnDestroy() {
    this.destroy.next(null);
  }

}
