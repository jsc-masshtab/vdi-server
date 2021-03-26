import { CUSTOM_ELEMENTS_SCHEMA, NO_ERRORS_SCHEMA } from '@angular/core';
import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { RouterTestingModule } from '@angular/router/testing';
import { MatDialog } from '@angular/material/dialog';
import { of } from 'rxjs';

import { GroupsComponent } from './groups.component';
import { GroupsService } from '../groups.service';

describe('GroupsComponent', () => {
  let component: GroupsComponent;
  let fixture: ComponentFixture<GroupsComponent>;

  let serviceStub: Partial<GroupsService>;

  beforeEach(async(() => {
    serviceStub = {
      getGroups(): any {
        return {
          valueChanges: of({
            data: {
              groups: []
            }
          })
        };
      },
      paramsForGetUsers: {
        spin: false
      }
    };    

    TestBed.configureTestingModule({
      imports: [ RouterTestingModule ],
      declarations: [GroupsComponent ],
      providers: [
        {
          provide: MatDialog,
          useValue: {}
        },
        {
          provide: GroupsService,
          useValue: serviceStub
        }
      ],
      schemas: [
        CUSTOM_ELEMENTS_SCHEMA,
        NO_ERRORS_SCHEMA
      ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(GroupsComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
