import { CUSTOM_ELEMENTS_SCHEMA, NO_ERRORS_SCHEMA } from '@angular/core';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { waitForAsync, ComponentFixture, TestBed } from '@angular/core/testing';
import { MatDialogRef } from '@angular/material/dialog';

import { AddGroupComponent } from './add-groups.component';
import { GroupsService } from '../groups.service';

describe('AddGroupComponent', () => {
  let component: AddGroupComponent;
  let fixture: ComponentFixture<AddGroupComponent>;

  let serviceStub: Partial<GroupsService>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      imports: [
        ReactiveFormsModule,
        FormsModule
      ],
      declarations: [ AddGroupComponent ],
      providers: [
        {
          provide: GroupsService,
          useValue: serviceStub
        },
        {
          provide: MatDialogRef,
          useValue: {}
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
    fixture = TestBed.createComponent(AddGroupComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
