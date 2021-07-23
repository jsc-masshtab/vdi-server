import { CUSTOM_ELEMENTS_SCHEMA } from '@angular/core';
import { waitForAsync, ComponentFixture, TestBed } from '@angular/core/testing';
import { RouterTestingModule } from '@angular/router/testing';
import { MatDialog } from '@angular/material/dialog';
import { of } from 'rxjs';

import { GroupsDetailsComponent } from './groups-details.component';
import { GroupsService} from '../groups.service';

describe('GroupsDetailsComponent', () => {
  let component: GroupsDetailsComponent;
  let fixture: ComponentFixture<GroupsDetailsComponent>;

  let serviceStub: Partial<GroupsService>;

  beforeEach(waitForAsync(() => {
    serviceStub = {
      getGroup(): any {
        return of({
          data: {
            group: {}
          }
        })
      },
    };

    TestBed.configureTestingModule({
      imports: [ RouterTestingModule ],
      declarations: [ GroupsDetailsComponent ],
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
        CUSTOM_ELEMENTS_SCHEMA
      ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(GroupsDetailsComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
