import { CUSTOM_ELEMENTS_SCHEMA, NO_ERRORS_SCHEMA } from '@angular/core';
import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { MatDialogRef, MAT_DIALOG_DATA } from '@angular/material/dialog';

import { RemoveUserGroupComponent } from './remove-user.component';
import { GroupsService } from '../../groups.service';

describe('RemoveUserGroupComponent', () => {
  let component: RemoveUserGroupComponent;
  let fixture: ComponentFixture<RemoveUserGroupComponent>;

  let serviceStub: Partial<GroupsService>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ RemoveUserGroupComponent ],
      providers: [
        {
          provide: MatDialogRef,
          useValue: {}
        },
        {
          provide: MAT_DIALOG_DATA,
          useValue: {}
        },
        {
          provide: GroupsService,
          useValue: serviceStub
        },
      ],
      schemas: [
        CUSTOM_ELEMENTS_SCHEMA,
        NO_ERRORS_SCHEMA
      ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(RemoveUserGroupComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
